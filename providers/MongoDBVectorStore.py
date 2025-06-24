from providers.VectorStoreStrategy import VectorStoreStrategy


class MongoDBVectorStore(VectorStoreStrategy):
    def __init__(
        self, collection, index_name="vector_index", embedding_path="embedding"
    ):
        self.collection = collection
        self.index_name = index_name
        self.embedding_path = embedding_path

    def search_similar(self, embedding, top_k=5):
        pipeline = [
            {
                "$vectorSearch": {
                    "index": self.index_name,
                    "queryVector": embedding.tolist(),
                    "path": self.embedding_path,
                    "numCandidates": top_k * 2,
                    "limit": top_k,
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
        return list(self.collection.aggregate(pipeline))
