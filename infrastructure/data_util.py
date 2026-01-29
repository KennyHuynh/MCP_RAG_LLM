from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader, TextLoader

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
