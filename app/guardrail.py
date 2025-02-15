import concurrent.futures
import logging

from huggingface import Embedding
from providers import VectorStore, Sanitize, AnomalyDetection

from pydantic import BaseModel
from enum import Enum
import numpy as np

import torch.nn.functional as F
import math 

from collections import Counter
import nltk
nltk.download('punkt') 

class StoreType(str, Enum):
    FAISS = "FAISS"
    ATLAS = "ATLAS"


class VectorStoreType(BaseModel):
    type: StoreType
    address: str | None = None


class Guardrail:
    def __init__(
        self,
        model: str | None,
        langfuse: str | None,
        vector_store: VectorStoreType,
        similarity_upper_bound: float = 0.8,
        anomaly_upper_bound: float = 0.8,
        entropy_upper_bound: float = 0.8,
    ):
        if vector_store is None:
            raise ValueError("A vector is required")

        self.model = model
        self.langfuse = langfuse
        self.vector_store = VectorStore.config_vector_store(vector_store)

        self.similarity_upper_bound = similarity_upper_bound
        self.anomaly_upper_bound = anomaly_upper_bound
        self.entropy_upper_bound = entropy_upper_bound

    def should_block(self, query) -> dict[str, bool | str | None]:
        if Sanitize.contains_invisible_characters(query):
            return {"blocked": True, "reason": "invisible characters"}
        
        query_embedding = Embedding.transform(query)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_malicious_similarity = executor.submit(
                self.query_malicious_similarity, query_embedding
            )
            future_anomaly = executor.submit(
                self.query_anomaly_detection, query_embedding
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
        if validation_model_prediction.get("prediction") == "malicious":
            return {"blocked": True, "reason": "validation model block"}

        return {"blocked": False, "reason": None}

    def query_entropy(self, query: str):
        tokens = nltk.word_tokenize(query)
        total_tokens = len(tokens)
        if total_tokens == 0:
            return 0.0
        freq = Counter(tokens)
        entropy = sum(-p * math.log2(p) for p in (count / total_tokens for count in freq.values()))
        return entropy
       
    def query_anomaly_detection(self, query: str) -> tuple[str, float]:
        model, vectorizer = AnomalyDetection.bootstrap()
        token = vectorizer.transform([query])
        
        prediction: int = model.predict(token)
        anomaly_score: float = model.decision_function(token)

        result = "malicious" if prediction == 1 else "benign"
        
        logging.info(f"Prediction: {result}")
        logging.info(f"Anomaly Score: {anomaly_score}")
    
        return result, anomaly_score

    def query_malicious_similarity(self, query_embedding):
        similar_embedding = self.vector_store.find_similar(query_embedding)
        return similar_embedding

    def invoke_validation_model(self, query):
        return {"prediction": "malicious"}

    def compute_score(self, malicious_similarity, anomaly, entropy):
        weights = np.array([3.0, 2.0, 1.0])
        values = np.array([malicious_similarity, anomaly, entropy]) * weights
        exp_values = np.exp(values - np.max(values))  
        softmax_scores = exp_values / np.sum(exp_values)
        return np.sum(softmax_scores)