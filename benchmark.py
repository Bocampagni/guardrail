import argparse
import logging
import random
import time

import faiss
from datasets import load_dataset

from guardrail import Guardrail

RANDOM_SEED = random.randint(0, 1000)


def load_test_data(num_queries=100):
    print(f"Loading dataset with {num_queries} queries...")
    ds = load_dataset("reshabhs/SPML_Chatbot_Prompt_Injection")
    return ds["train"].shuffle(seed=RANDOM_SEED).select(range(num_queries))


def setup_vector_store():
    print("Setting up FAISS guardrail...")
    return faiss.read_index("./adhoc/models/malicious_embeddings.index")


def setup_configuration(mode="parallel"):
    if mode == "sequential":
        print("Running in sequential mode...")
        return {
            "similarity_upper_bound": 0.8,
            "anomaly_upper_bound": 0.02,
            "entropy_upper_bound": 4.2,
            "genai_upper_bound": 0.90,
            "pipeline": True,
        }
    else:
        print("Running in parallel mode...")
        return {
            "similarity_upper_bound": 0.8,
            "anomaly_upper_bound": 0.02,
            "entropy_upper_bound": 4.2,
            "genai_upper_bound": 0.90,
            "decision_threshold": 0.5,
            "pipeline": False,
        }


def main():
    parser = argparse.ArgumentParser(description="Run guardrail benchmark")
    parser.add_argument(
        "--mode",
        default="parallel",
        choices=["sequential", "parallel"],
        help="Execution mode (default: parallel)",
    )
    parser.add_argument(
        "--queries",
        type=int,
        default=100,
        help="Number of queries to test (default: 100)",
    )
    args = parser.parse_args()

    print(f"Running benchmark in {args.mode} mode with {args.queries} queries...")

    config = setup_configuration(args.mode)
    test_data = load_test_data(args.queries)
    faiss_index = setup_vector_store()

    guardrail = Guardrail(
        vector_store=faiss_index,
        **config,
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

        if result["blocked"]:
            blocked_count += 1

        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{args.queries} queries...")

    total_time = time.time() - start_time
    accuracy = correct_predictions / len(test_data)
    avg_time_per_query = total_time / len(test_data)

    print("\n=== Results ===")
    print(f"Total queries: {len(test_data)}")
    print(f"Blocked queries: {blocked_count}")
    print(f"Accuracy: {accuracy:.3f}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Avg time per query: {avg_time_per_query * 1000:.2f}ms")
    print(f"Throughput: {len(test_data) / total_time:.2f} queries/second")


if __name__ == "__main__":
    main()
