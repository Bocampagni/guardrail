import joblib
import os 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import OneClassSVM

def load_resource(path: str) -> object:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Resource not found at {path}")
    
    return joblib.load(path)

def bootstrap() -> tuple[OneClassSVM, TfidfVectorizer]:
    model: OneClassSVM = load_resource("../models/ocsvm_model.pkl")
    vectorizer: TfidfVectorizer = load_resource("../models/vectorizer.pkl")
    return model, vectorizer