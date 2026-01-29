import os
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
# In 2026, many indexing tools have stabilized in 'langchain.indexes'
# but 'langchain_classic' remains a valid path for specific ReAct agents.
from langchain_classic.indexes import SQLRecordManager, index
from langchain_huggingface import HuggingFaceEmbeddings
import json
from langchain_core.documents import Document


class RAGStorage:
    def __init__(self, db_path="./rag_internal_db", record_db="sqlite:///rag_internal_record_manager.db"):
        self.db_path = db_path
        self.embeddings = HuggingFaceEmbeddings(
            model="paraphrase-multilingual-MiniLM-L12-v2")

        # Initialize the Vector Store with a persistent directory
        self.vector_store = Chroma(
            collection_name="internal_knowledge",
            embedding_function=self.embeddings,
            persist_directory=self.db_path
        )

        # Initialize the Record Manager (tracks hashes in a separate SQLite DB)
        namespace = "chroma/internal_knowledge"
        self.record_manager = SQLRecordManager(namespace, db_url=record_db)
        self.record_manager.create_schema()

        if len(self.vector_store.get()['ids']) == 0:
            # Load initial data using the deduplication logic
            self._init_db('./infrastructure/rag_data/ae_rag_data.json')

    def _init_db(self):
        # 1. Define your initial content
        initial_docs = [
            Document(
                page_content="""# Action: Fill Form Field
Description: Fills a text field or form input with a specific value.
Code: await page.fill('selector', 'value');""",
                metadata={
                    "source": "playwright_docs",
                    "category": "action",
                    "function": "fill",
                    "framework": "playwright",
                    "language": "typescript"
                }
            ),
            Document(
                page_content="""# Action: Mouse Click
Description: Performs a mouse click on the element matching the selector.
Code: await page.click('selector');""",
                metadata={
                    "source": "playwright_docs",
                    "category": "action",
                    "function": "click",
                    "framework": "playwright",
                    "language": "typescript"
                }
            ),
            Document(
                page_content="""# Assertion: Validate URL
Description: Verifies that the current page URL matches a specific pattern (regex) or string.
Code: await expect(page).toHaveURL(/.*my-account/);""",
                metadata={
                    "source": "playwright_docs",
                    "category": "assertion",
                    "function": "toHaveURL",
                    "framework": "playwright",
                    "language": "typescript"
                }
            )
        ]

        # 3. Use the Indexing API with 'incremental' cleanup.
        # This will:
        # - Hash the 'combined_doc'.
        # - Check if this hash + source ('playwright_docs') already exists in record_manager.db.
        # - If it exists and hasn't changed, it SKIPS the embedding and storage steps.
        indexing_result = index(
            initial_docs,
            self.record_manager,
            self.vector_store,
            cleanup="incremental",  # Ensures updates are processed but duplicates are skipped
            source_id_key="source"
        )

        # If 'num_added' is 0, it means the document already existed and was skipped.
        print(f"Indexing complete: {indexing_result}")

    def _init_db(self, json_data_path: str):

        # Load data from JSON file
        with open(json_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        initial_docs = []

        for item in data:
            page_content = f"""
        Flow ID: {item['id']}
        Scope: {item['scope']}
        Description: {item['description']}

        Target URL:
        {item['target_url']}

        Discovery Goals:
        {json.dumps(item['discovery_goals'], indent=2)}

        Expected Behavior:
        {json.dumps(item['expected_behavior'], indent=2)}

        Technical Guidelines:
        {json.dumps(item['technical_guidelines'], indent=2)}
        """.strip()

            metadata = {
                "id": item["id"],
                "scope": item["scope"],
                "target_url": item["target_url"],
                "search_keywords": item["search_keywords"]
            }

            doc = Document(
                page_content=page_content,
                metadata=metadata
            )

            initial_docs.append(doc)

            # Index documents with deduplication
            indexing_result = index(
                initial_docs,
                self.record_manager,
                self.vector_store,
                cleanup="incremental",
                source_id_key="id"
            )

        print(f"Indexing complete: {indexing_result}")

    def search_documents(self, query: str):
        print(f"--- [RAG Search] Finding data for user's query: {query} ---")
        results = self.vector_store.similarity_search(query, k=3)
        return results

if __name__ == "__main__":
    rag = RAGStorage()
    # rag.search_documents("Show me how to login to my account page.")
    # res = rag.search_documents("What is mouse click?")
    # print(f"Response:\n{res}")
