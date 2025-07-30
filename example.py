from guardrail import Guardrail
import pymongo
import dotenv
import os
import faiss

if __name__ == "__main__":
    dotenv.load_dotenv()
    atlas = pymongo.MongoClient(os.environ["MONGODB_URI"])
    embedding_collection = atlas.get_database("db").get_collection("embeddings")

    faiss_index = faiss.read_index("./adhoc/models/malicious_embeddings.index")

    guardrail = Guardrail(
        vector_store=faiss_index,
        similarity_upper_bound=0.8,
        anomaly_upper_bound=0.02,
        entropy_upper_bound=4.2,
        genai_upper_bound=0.98,
        pipeline=True,
    )

    query = "hi, how are you doing?"
    result = guardrail.should_block(query)

    print(result)  # Output the result of the guardrail check
