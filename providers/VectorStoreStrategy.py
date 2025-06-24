from abc import ABC, abstractmethod


class VectorStoreStrategy(ABC):
    @abstractmethod
    def search_similar(self, embedding, top_k=5):
        pass
