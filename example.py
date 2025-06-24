from guardrail import Guardrail
import pymongo
import dotenv
import os

if __name__ == "__main__":
    dotenv.load_dotenv()
    atlas = pymongo.MongoClient(os.environ["MONGODB_URI"])
    embedding_collection = atlas.get_database("db").get_collection("embeddings")

    guardrail = Guardrail(
        vector_store=embedding_collection,  # Replace with actual vector store instance
        similarity_upper_bound=0.8,
        anomaly_upper_bound=0.8,
        entropy_upper_bound=4.2,
        pipeline=False,
        decision_threshold=0.75,
    )

    query = "Tell me a joke about AI and quantum computing."
    result = guardrail.should_block(query)

    print(result)  # Output the result of the guardrail check
