import json
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader, TextLoader
from typing import List
from pathlib import Path
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import JSONLoader
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter

# def load_entire_knowledge_base(directory_path: str):

#     # 1. Load JSON/TXT as raw text (prevents the Unstructured Schema error)
#     text_loader = DirectoryLoader(
#         directory_path,
#         glob="**/*.json",
#         loader_cls=JSONLoader,
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
) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    base_path = Path(directory_path)
    if not base_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    all_processed_chunks = []
    total_files = 0

    for file_path in base_path.rglob("*"):
        if not file_path.is_file():
            continue

        total_files += 1
        suffix = file_path.suffix.lower()

        try:
            # ---- XỬ LÝ RIÊNG FILE JSON (Bóc tách từng Test Case) ----
            if suffix == ".json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Nếu JSON là list các object (như data của bạn)
                    if isinstance(data, list):
                        for item in data:
                            # Tạo nội dung search tập trung vào Intent và Tags
                            content = f"TestID: {item.get('test_id')}\n" \
                                      f"Summary: {item.get('intent', {}).get('summary')}\n" \
                                      f"Scope: {item.get('scope')}\n" \
                                      f"Tags: {', '.join(item.get('tags', []))}"

                            doc = Document(
                                page_content=content,
                                metadata={
                                    "source": file_path.name,
                                    "test_id": item.get("test_id"),
                                    "category": item.get("tags")[0] if item.get("tags") else "general"
                                }
                            )
                            # Chunk nhỏ dữ liệu JSON (thường JSON test case đã nhỏ sẵn)
                            all_processed_chunks.extend(splitter.split_documents([doc]))
                continue # Đã xử lý xong JSON, nhảy sang file tiếp theo

            # ---- XỬ LÝ MD ----
            if suffix == ".md":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                # 1. Define the headers to split on (Mapping # Flow and ## STEP to metadata)
                headers_to_split_on = [("#", "flow_id"), ("##", "test_id")]

                md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
                md_header_splits = md_splitter.split_text(data)

                # 2. Clean up the 'test_id' (Removing 'STEP 1: ' prefix to match BENCHMARK_SUITE)
                for doc in md_header_splits:
                    raw_test_id = doc.metadata.get("test_id", "")
                    if ":" in raw_test_id:
                        doc.metadata["test_id"] = raw_test_id.split(":")[-1].strip()
                    raw_flow_id = doc.metadata.get("flow_id", "")
                    if ":" in raw_flow_id:
                        doc.metadata["flow_id"] = raw_flow_id.split(":")[-1].strip()
                # Add common metadata
                doc.metadata["source"] = file_path.name
                all_processed_chunks.extend(splitter.split_documents(md_header_splits))
                continue # Đã xử lý xong MD, nhảy sang file tiếp theo

            # ---- XỬ LÝ TXT, CSV... ----
            docs = [] # Initialize to avoid NameError
            if suffix in {".txt", ".csv", ".yaml", ".yml"}:
                loader = TextLoader(str(file_path), encoding="utf-8")
                docs = loader.load()

            # ---- XỬ LÝ BINARY (PDF, DOCX...) ----
            else:
                loader = UnstructuredFileLoader(str(file_path))
                docs = loader.load()

            # Thêm metadata source cho các file không phải JSON
            if docs:
                for d in docs:
                    d.metadata["source"] = file_path.name
                all_processed_chunks.extend(splitter.split_documents(docs))

        except Exception as e:
            print(f"⚠️ Skipped {file_path.name}: {e}")

    print(f"✅ Processed {total_files} files into {len(all_processed_chunks)} chunks.")
    return all_processed_chunks # Trả về list documents để lưu vào VectorDB