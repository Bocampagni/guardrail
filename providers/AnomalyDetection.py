import joblib
import os 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import OneClassSVM

def bootstrap() -> tuple[OneClassSVM, TfidfVectorizer]:
    model: OneClassSVM = joblib.load("./models/ocsvm_model.pkl")
    vectorizer: TfidfVectorizer = joblib.load("./models/vectorizer.pkl")
    return model, vectorizer