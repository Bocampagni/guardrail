import time
import faiss
from datasets import load_dataset
from guardrail import Guardrail
import logging


NUMBER_OF_QUERIES = 1000


def main():
    print("Loading dataset...")
    ds = load_dataset("reshabhs/SPML_Chatbot_Prompt_Injection")
    test_data = ds["train"].shuffle(seed=42).select(range(NUMBER_OF_QUERIES))

    print("Setting up FAISS guardrail...")
    faiss_index = faiss.read_index("./adhoc/models/malicious_embeddings.index")
    guardrail = Guardrail(
        vector_store=faiss_index,
        similarity_upper_bound=0.8,
        anomaly_upper_bound=0.02,
        entropy_upper_bound=4.2,
        genai_upper_bound=0.90,
        decision_threshold=0.5,
        pipeline=False,
    )

    print("Running benchmark...")
    start_time = time.time()

    blocked_count = 0
    correct_predictions = 0

    for i, item in enumerate(test_data):
        query = item["User Prompt"]
        true_label = item["Prompt injection"]  # 1 = malicious, 0 = benign
        try:
            result = guardrail.should_block(query)
        except Exception as e:
            logging.error(f"Error processing query '{query}': {e}")
            continue
        predicted_malicious = 1 if result["blocked"] else 0

        if predicted_malicious == true_label:
            correct_predictions += 1
        else:
            print("Discrepancy...")
            print(result["scores"])

        if result["blocked"]:
            blocked_count += 1

        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/1000 queries...")

    total_time = time.time() - start_time
    accuracy = correct_predictions / len(test_data)
    avg_time_per_query = total_time / len(test_data)

    print(f"\n=== Results ===")
    print(f"Total queries: {len(test_data)}")
    print(f"Blocked queries: {blocked_count}")
    print(f"Accuracy: {accuracy:.3f}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Avg time per query: {avg_time_per_query * 1000:.2f}ms")
    print(f"Throughput: {len(test_data) / total_time:.2f} queries/second")


if __name__ == "__main__":
    main()
