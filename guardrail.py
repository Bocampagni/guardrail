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
nltk.download("punkt_tab")


class Guardrail:
    def __init__(
        self,
        vector_store: pymongo.collection.Collection | faiss.Index,
        similarity_upper_bound: float = 0.8,
        anomaly_upper_bound: float = 0.8,
        entropy_upper_bound: float = 0.8,
    ):
        self.vector_store = vector_store
        self.similarity_upper_bound = similarity_upper_bound
        self.anomaly_upper_bound = anomaly_upper_bound
        self.entropy_upper_bound = entropy_upper_bound

    def should_block(self, query) -> dict[str, bool | str | None]:
        if Sanitize.contains_invisible_characters(query):
            return {"blocked": True, "reason": "invisible characters"}

        malicious_similarity = self.query_malicious_similarity(query)
        if malicious_similarity > self.similarity_upper_bound:
            return {"blocked": True, "reason": "malicious similarity above threshold"}

        anomaly, anomaly_score = self.query_anomaly_detection(query)
        if anomaly == "Anomaly" and abs(anomaly_score) < self.anomaly_upper_bound:
            return {"blocked": True, "reason": "anomaly score above threshold"}

        entropy_score = self.query_entropy(query)
        if entropy_score > self.entropy_upper_bound:
            return {"blocked": True, "reason": "entropy score above threshold"}

        validation_model_prediction = self.invoke_validation_model(query)
        if validation_model_prediction.get("prediction") == "INJECTION":
            return {"blocked": True, "reason": "validation model block"}

        return {"blocked": False, "reason": "no reason"}

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
        token = vectorizer.transform([query]).toarray()

        prediction: int = model.predict(token)
        anomaly_score: float = model.decision_function(token)[0]

        result = "Normal" if prediction == 1 else "Anomaly"

        logging.info(f"Prediction: {result}")
        logging.info(f"Anomaly Score: {anomaly_score}")

        return result, abs(anomaly_score)  ##  Quanto menor, mais anômalo

    def query_malicious_similarity(self, query: str) -> float:
        embedding = Embedding.transform(query)
        if isinstance(self.vector_store, pymongo.collection.Collection):
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "queryVector": embedding.tolist(),
                        "path": "embedding",
                        "numCandidates": 5,
                        "limit": 5,
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "text": 1,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
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
