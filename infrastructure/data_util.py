from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader, TextLoader
from pathlib import Path
from typing import List
from streamlit.runtime.uploaded_file_manager import UploadedFile

def load_entire_knowledge_base(directory_path: str):

    # 1. Load JSON/TXT as raw text (prevents the Unstructured Schema error)
    text_loader = DirectoryLoader(
        directory_path,
        glob="**/*.json",
        loader_cls=TextLoader,
        silent_errors=True,
        show_progress=True,
        use_multithreading=True,
    )

    # USE [Unstructured](https://python.langchain.com) to load various document types
    # Install unstructured library: pip install "unstructured[all-docs]"
    binary_loader = DirectoryLoader(
        path=directory_path,
        glob="**/*.[!json]*",
        loader_cls=UnstructuredFileLoader,
        show_progress=True,
        use_multithreading=True,
        silent_errors=True
    )

    docs = text_loader.load() + binary_loader.load()
    print(f"Successfully loaded {len(docs)} documents from the data repository.")
    return docs

def save_uploaded_files(uploaded_files, save_dir: str = "./infrastructure/rag_data_example/uploaded"):

    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    saved_files = []

    for uploaded_file in uploaded_files:
        file_path = save_path / uploaded_file.name

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        saved_files.append(str(file_path))

    return saved_files
