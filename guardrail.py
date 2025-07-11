import logging
import nltk
import pymongo
import faiss
import math
import pymongo.collection
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union

from huggingface import Embedding, Deberta
from providers import Sanitize, AnomalyDetection
from collections import Counter
from providers.MongoDBVectorStore import MongoDBVectorStore
from providers.FaissVectorStore import FaissVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

nltk.download("punkt")
nltk.download("punkt_tab")


def query_entropy(query: str) -> float:
    tokens = nltk.word_tokenize(query)
    total_tokens = len(tokens)
    if total_tokens == 0:
        return 0.0
    freq = Counter(tokens)
    entropy = sum(
        -p * math.log2(p) for p in (count / total_tokens for count in freq.values())
    )
    logging.info(f"Entropy: {entropy}")
    return entropy


def query_anomaly_detection(query: str) -> tuple[str, float]:
    model, vectorizer = AnomalyDetection.bootstrap()
    token = vectorizer.transform([query]).toarray()

    prediction: int = model.predict(token)
    anomaly_score: float = model.decision_function(token)[0]

    result = "Normal" if prediction == 1 else "Anomaly"

    logging.info(f"Prediction: {result}")
    logging.info(f"Anomaly Score: {anomaly_score}")

    return result, abs(anomaly_score)  ##  Quanto menor, mais anômalo


def query_malicious_similarity(
    query: str, vector_store: pymongo.collection.Collection | faiss.Index, top_k=1
) -> float:
    embedding = Embedding.transform(query)
    results = vector_store.search_similar(embedding, top_k)

    if not results:
        return 0.0

    return results[0].get("score", 0.0)


def invoke_validation_model(query):
    classified_text = Deberta.classify_text(query)
    text = classified_text[0]["label"]
    score = classified_text[0]["score"]

    logging.info(f"Validation Model Prediction: {text}")
    logging.info(f"Validation Model Score: {score}")

    return {"prediction": text, "score": score}


class Guardrail:
    def __init__(
        self,
        vector_store: Union[pymongo.collection.Collection | faiss.Index],
        similarity_upper_bound: float = 0.8,
        anomaly_upper_bound: float = 0.8,
        entropy_upper_bound: float = 0.8,
        vector_store_strategy=None,
        pipeline=True,
        decision_threshold: Union[float, None] = None,
    ):
        if not pipeline and not decision_threshold:
            raise ValueError(
                "decision_threshold must be set if pipeline is False (mxiture of experts approach)"
            )

        self.vector_store = vector_store
        self.similarity_upper_bound = similarity_upper_bound
        self.anomaly_upper_bound = anomaly_upper_bound
        self.entropy_upper_bound = entropy_upper_bound
        self.vector_store_strategy = (
            vector_store_strategy or self.create_vector_store_strategy(vector_store)
        )
        self.is_pipeline = pipeline
        self.decision_threshold = decision_threshold

    def should_block(self, query) -> dict[str, bool | str | None]:
        if self.is_pipeline:
            if Sanitize.contains_invisible_characters(query):
                return {"blocked": True, "reason": "invisible characters"}

            malicious_similarity = query_malicious_similarity(
                query, self.vector_store_strategy
            )
            if malicious_similarity > self.similarity_upper_bound:
                return {
                    "blocked": True,
                    "reason": "malicious similarity above threshold",
                }

            anomaly, anomaly_score = query_anomaly_detection(query)
            if anomaly == "Anomaly" and abs(anomaly_score) < self.anomaly_upper_bound:
                return {"blocked": True, "reason": "anomaly score above threshold"}

            entropy_score = query_entropy(query)
            if entropy_score > self.entropy_upper_bound:
                return {"blocked": True, "reason": "entropy score above threshold"}

            validation_model_prediction = invoke_validation_model(query)
            if validation_model_prediction.get("prediction") == "INJECTION":
                return {"blocked": True, "reason": "validation model block"}

            return {"blocked": False, "reason": "no reason"}
        else:
            logging.info(
                f"Running expert mix approach with decision threshold: {self.decision_threshold}"
            )
            if Sanitize.contains_invisible_characters(query):
                return {"blocked": True, "reason": "invisible characters"}

            results = {}
            try:
                with ThreadPoolExecutor(max_workers=4) as executor:
                    future_to_expert = {
                        executor.submit(
                            query_malicious_similarity,
                            query,
                            self.vector_store_strategy,
                        ): "malicious_similarity",
                        executor.submit(
                            query_anomaly_detection, query
                        ): "anomaly_detection",
                        executor.submit(query_entropy, query): "entropy",
                        executor.submit(
                            invoke_validation_model, query
                        ): "validation_model",
                    }

                    for future in as_completed(future_to_expert):
                        expert_name = future_to_expert[future]
                        try:
                            results[expert_name] = future.result()
                        except Exception as e:
                            logging.error(f"Error in {expert_name}: {e}")
                            results[expert_name] = None

            except Exception as e:
                logging.error(f"Parallel execution failed: {e}")
                return {"blocked": False, "reason": "error during parallel execution"}

            malicious_similarity = results.get("malicious_similarity", 0.0)
            anomaly_result, anomaly_score = results.get(
                "anomaly_detection", ("Normal", 1.0)
            )
            entropy_score = results.get("entropy", 0.0)
            validation_model_prediction = results.get(
                "validation_model", {"prediction": "INJECTION", "score": 0.0}
            )

            normalized_malicious = min(
                malicious_similarity / self.similarity_upper_bound, 1.0
            )
            normalized_anomaly = (
                (1 - abs(anomaly_score) / self.anomaly_upper_bound)
                if anomaly_result == "Anomaly"
                else 0.0
            )
            normalized_entropy = min(entropy_score / self.entropy_upper_bound, 1.0)
            normalized_validation = (
                validation_model_prediction.get("score", 0.0)
                if validation_model_prediction.get("prediction") == "INJECTION"
                else 0.0
            )

            # Compute weighted score using expert mix
            combined_score = self.compute_score(
                normalized_malicious,
                normalized_anomaly,
                normalized_entropy,
                normalized_validation,
            )

            # Log scores for debugging
            logging.info(
                f"Normalized scores - Malicious: {normalized_malicious}, Anomaly: {normalized_anomaly}, Entropy: {normalized_entropy}, Validation: {normalized_validation}"
            )
            logging.info(f"Combined Score: {combined_score}")

            scores = {
                "malicious_similarity": normalized_malicious,
                "anomaly": normalized_anomaly,
                "entropy": normalized_entropy,
                "validation_model": normalized_validation,
                "combined": combined_score,
            }

            # Decision threshold
            if combined_score > self.decision_threshold:
                return {
                    "blocked": True,
                    "reason": "combined score above threshold",
                    "scores": scores,
                }

            return {
                "blocked": False,
                "reason": "no reason",
                "scores": scores,
            }

    def compute_score(self, malicious_similarity, anomaly, entropy, validation_score):
        return (malicious_similarity + anomaly + entropy + validation_score) / 4

    def create_vector_store_strategy(self, vector_store):
        if isinstance(vector_store, pymongo.collection.Collection):
            return MongoDBVectorStore(vector_store)
        elif isinstance(vector_store, faiss.Index):
            return FaissVectorStore(vector_store)
        else:
            raise ValueError(f"Unsupported vector store type: {type(vector_store)}")
