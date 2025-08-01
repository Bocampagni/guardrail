import numpy as np

from providers.VectorStoreStrategy import VectorStoreStrategy


class FaissVectorStore(VectorStoreStrategy):
    def __init__(self, index):
        self.index = index

    def search_similar(self, embedding, top_k=5):
        scores, indices = self.index.search(np.array([embedding]), top_k)
        return [
            {"score": float(scores[0][i]), "index": int(indices[0][i])}
            for i in range(len(indices[0]))
            if indices[0][i] >= 0
        ]
