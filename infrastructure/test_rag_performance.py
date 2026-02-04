from test_rag_storage import build_vector_store, search_documents
from data_util import load_entire_knowledge_base
from typing import List
from langchain_core.documents import Document

# Bộ câu hỏi Benchmark cho dữ liệu Automation
# BENCHMARK_SUITE = [
#     {"query": "how to walking the dog", "expected_id": "ae_login_flow", "scope": "Authentication"},
#     {"query": "Add product to shopping cart", "expected_id": "ae_add_to_cart", "scope": "Product Interaction"},
#     {"query": "Verify user credentials and dashboard access", "expected_id": "ae_login_flow", "scope": "Authentication"},
#     {"query": "Steps for product interaction", "expected_id": "ae_add_to_cart", "scope": "Product Interaction"}
# ]
# DIR_DATA = "./infrastructure/rag_data_example/rag_data"

BENCHMARK_SUITE = [
    {"query": "Describe the checkout process from login to payment.", "expected_id": "UNKNOWN_STAGE"},
    {"query": "Which steps involve clicking buttons?", "expected_id": "LOGIN_STAGE"},
    {"query": "How does the user log in?", "expected_id": "LOGIN_STAGE"},
    {"query": "How is a product added to the cart?", "expected_id": "ADD_TO_CART_STAGE"},
]
DIR_DATA = "./infrastructure/rag_data_example/md_data"

def calculate_hit_rate(
    queries: List[dict],
    retrieved_docs: List[List[Document]],
    source_key: str = "test_id" # Changed to match your BENCHMARK_SUITE keys
) -> float:
    hits = 0

    for i, query_item in enumerate(queries):
        query_text = query_item["query"]
        # Ensure 'expected' is a set of strings, even if input is a single string
        expected_val = query_item["expected_id"]
        expected_set = {expected_val} if isinstance(expected_val, str) else set(expected_val)
        
        # Extract IDs from retrieved documents
        retrieved_ids = {
            doc.metadata.get(source_key)
            for doc in retrieved_docs[i]
        }

        # Check for intersection
        is_hit = not expected_set.isdisjoint(retrieved_ids)
        if is_hit:
            hits += 1

        # Detailed Logging
        status = "✅ [HIT]" if is_hit else "❌ [MISS]"
        print(f"{status}")
        print(f"  Query: '{query_text}'")
        print(f"  Expected: {expected_set}")
        print(f"  Actual:   {retrieved_ids}")
        print("-" * 30)

    total_rate = hits / len(queries) if queries else 0.0
    print(f"FINAL HIT RATE: {total_rate:.2%}")
    return total_rate

def test_rag_hit_rate():
    # 1. Load documents
    documents = load_entire_knowledge_base(DIR_DATA)

    # 2. Build vector DB
    vectordb = build_vector_store(documents)

    # 4. Retrieve docs
    retrieved_docs = []
    for q in BENCHMARK_SUITE:
        results_with_score = search_documents(vectordb, q["query"], top_k=3)
        print(f"\nScores for '{q['query']}':")
        for doc, score in results_with_score:
            print(f" - {doc.metadata.get('test_id')}: {score:.4f}")
        # Filter out results that are below the threshold
        filtered_docs = [doc for doc, score in results_with_score if score >= 0.4]
        retrieved_docs.append(filtered_docs)

    # 5. Evaluate hit rate
    hit_rate = calculate_hit_rate(BENCHMARK_SUITE, retrieved_docs)

    assert hit_rate >= 0.5, f"Hit rate {hit_rate:.2%} is below the acceptable threshold."

if __name__ == "__main__":
    test_rag_hit_rate()