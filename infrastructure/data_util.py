from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader, TextLoader
from typing import Iterator
from pathlib import Path
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter

# def load_entire_knowledge_base(directory_path: str):

#     # 1. Load JSON/TXT as raw text (prevents the Unstructured Schema error)
#     text_loader = DirectoryLoader(
#         directory_path,
#         glob="**/*.json",
#         loader_cls=TextLoader,
#         silent_errors=True,
#         show_progress=True,
#         use_multithreading=True,
#     )

#     # USE [Unstructured](https://python.langchain.com) to load various document types
#     # Install unstructured library: pip install "unstructured[all-docs]"
#     binary_loader = DirectoryLoader(
#         path=directory_path,
#         glob="**/*.[!json]*",
#         loader_cls=UnstructuredFileLoader,
#         show_progress=True,
#         use_multithreading=True,
#         silent_errors=True
#     )

#     docs = text_loader.load() + binary_loader.load()
#     print(f"Successfully loaded {len(docs)} documents from the data repository.")
#     return docs

def load_entire_knowledge_base(
    directory_path: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> Iterator:
    """
    Stream and chunk documents from a large knowledge base.
    Safe for 1GB+ datasets.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    base_path = Path(directory_path)

    if not base_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    total_files = 0

    for file_path in base_path.rglob("*"):
        if not file_path.is_file():
            continue

        total_files += 1
        suffix = file_path.suffix.lower()

        try:
            # ---- TEXT FILES (JSON, TXT, MD, CSV, YAML) ----
            if suffix in {".json", ".txt", ".md", ".csv", ".yaml", ".yml"}:
                loader = TextLoader(str(file_path), encoding="utf-8")
                docs = loader.load()

            # ---- BINARY / COMPLEX FILES ----
            else:
                loader = UnstructuredFileLoader(str(file_path))
                docs = loader.load()

            # ---- CHUNK IMMEDIATELY ----
            for chunk in splitter.split_documents(docs):
                yield chunk

        except Exception as e:
            # Silent skip but traceable
            print(f"⚠️ Skipped {file_path.name}: {e}")

    print(f"✅ Scanned {total_files} files from knowledge base.")