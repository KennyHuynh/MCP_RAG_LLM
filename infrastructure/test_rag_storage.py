import os
import shutil
from typing import List
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


def build_vector_store(
    documents: List[Document],
    persist_directory: str = "./test_chroma_db",
    clear_existing: bool = True
):
    # 1. Clear existing database folder if requested
    if clear_existing and os.path.exists(persist_directory):
        # We use shutil.rmtree to wipe the entire folder
        shutil.rmtree(persist_directory)
        print(f"🧹 Cleared existing database at {persist_directory}")

    embeddings = HuggingFaceEmbeddings(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )

    vectordb = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    print(f"✅ Successfully indexed {len(documents)} chunks.")
    return vectordb


def search_documents(
    vectordb: Chroma,
    query: str,
    top_k: int = 5
):
    return vectordb.similarity_search(query, k=top_k)