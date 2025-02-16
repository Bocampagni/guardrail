import logging
import concurrent.futures
import nltk
import pymongo
import faiss
import math
import numpy as np
import pymongo.collection

from huggingface import Embedding, Deberta
from providers import Sanitize, AnomalyDetection
from collections import Counter

nltk.download("punkt")

class Guardrail:
    def __init__(
        self,
        model: str | None,
        langfuse: str | None,
        vector_store: pymongo.collection.Collection | faiss.Index ,
        similarity_upper_bound: float = 0.8,
        anomaly_upper_bound: float = 0.8,
        entropy_upper_bound: float = 0.8,
    ):
        self.model = model
        self.langfuse = langfuse
        self.vector_store = vector_store
        self.similarity_upper_bound = similarity_upper_bound
        self.anomaly_upper_bound = anomaly_upper_bound
        self.entropy_upper_bound = entropy_upper_bound

    def should_block(self, query) -> dict[str, bool | str | None]:
        if Sanitize.contains_invisible_characters(query):
            return {"blocked": True, "reason": "invisible characters"}
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_malicious_similarity = executor.submit(
                self.query_malicious_similarity, query
            )
            future_anomaly = executor.submit(
                self.query_anomaly_detection, query
            )
            future_entropy = executor.submit(
                self.query_entropy, query
            )

            malicious_similarity = future_malicious_similarity.result()
            _, anomaly_score = future_anomaly.result()
            entropy_score = future_entropy.result()

        score = self.compute_score(malicious_similarity, anomaly_score, entropy_score)
        if score > 0.8:
            return {"blocked": True, "reason": "compound score above threshold"}

        validation_model_prediction = self.invoke_validation_model(query)
        if validation_model_prediction.get("prediction") == "INJECTION":
            return {"blocked": True, "reason": "validation model block"}

        return {"blocked": False, "reason": None}

    def query_entropy(self, query: str) -> float:
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

    def query_anomaly_detection(self, query: str) -> tuple[str, float]:
        model, vectorizer = AnomalyDetection.bootstrap()
        token = vectorizer.transform([query])

        prediction: int = model.predict(token)
        anomaly_score: float = model.decision_function(token)

        result = "Normal" if prediction == 1 else "Anomaly"

        logging.info(f"Prediction: {result}")
        logging.info(f"Anomaly Score: {anomaly_score}")

        return result, anomaly_score

    def query_malicious_similarity(self, query: str) -> float:
        embedding = Embedding.transform(query)
        if isinstance(self.vector_store, pymongo.collection.Collection):
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "queryVector": embedding,
                        "path": "embedding",
                        "exact": True,
                        "limit": 1
                    }
                }, {
                    "$project": {
                        "_id": 0,
                        "text": 1,
                        "score": {
                        "$meta": "vectorSearchScore"
                        }
                    }
                }
            ]
            result = list(self.vector_store.aggregate(pipeline))
            return result[0]["score"] if result else 0.0
        else:
            _, indices = self.vector_store.search(np.array([embedding]), 1)
            return indices[0][0] if indices else 0.0

    def invoke_validation_model(self, query):
        classified_text = Deberta.classify_text(query)
        text = classified_text[0]["label"]
        score = classified_text[0]["score"]
        
        logging.info(f"Validation Model Prediction: {text}")
        logging.info(f"Validation Model Score: {score}")
        
        return {"prediction": text, "score": score} 
        
    def compute_score(self, malicious_similarity, anomaly, entropy):
        return (malicious_similarity + anomaly + entropy) / 3