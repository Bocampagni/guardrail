from sentence_transformers import SentenceTransformer

MODEL = "all-MiniLM-L6-v2"


def transform(query: str):
    embedding_model = SentenceTransformer(MODEL)
    return embedding_model.encode(query)
