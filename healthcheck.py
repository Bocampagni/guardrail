from providers import AnomalyDetection
from huggingface import Embedding, Deberta

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import OneClassSVM
from transformers import AutoTokenizer, AutoModelForSequenceClassification

if __name__ == '__main__':
    model: OneClassSVM = AnomalyDetection.load_resource("./models/ocsvm_model.pkl")
    vectorizer: TfidfVectorizer = AnomalyDetection.load_resource("./models/vectorizer.pkl")

    if not model or not vectorizer:
        raise FileNotFoundError("Anomaly detection model not found")

    embedding_model = SentenceTransformer(Embedding.MODEL)
    if not embedding_model:
        raise FileNotFoundError("Embedding model not found")

    inference_model_tokenizer = AutoTokenizer.from_pretrained(Deberta.TOKENIZER)
    inference_model = AutoModelForSequenceClassification.from_pretrained(Deberta.MODEL)
    
    if not inference_model_tokenizer or not inference_model:
        raise FileNotFoundError("Inference model not found")
    
    print("Healthcheck successful") 
     