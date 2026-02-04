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
    chunk_size: int = 4000,
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

                    # Nếu JSON là list test cases
                    if isinstance(data, list):
                        for item in data:
                            test_id = item.get("test_id", "unknown_test")
                            tags = item.get("tags", [])
                            scope = item.get("scope", "")
                            test_type = item.get("test_type", "")

                            # -------- 1. INTENT CHUNK (WHY) --------
                            intent = item.get("intent", {})
                            intent_content = (
                                f"Test ID: {test_id}\n"
                                f"Intent Summary: {intent.get('summary', '')}\n"
                                f"Business Value: {intent.get('business_value', '')}\n"
                                f"Scope: {scope}\n"
                                f"Test Type: {test_type}"
                            )

                            all_processed_chunks.append(
                                Document(
                                    page_content=intent_content,
                                    metadata={
                                        "source": file_path.name,
                                        "test_id": test_id,
                                        "section": "intent",
                                        "scope": scope,
                                        "tags": ",".join(tags)
                                    }
                                )
                            )

                            # -------- 2. UI ELEMENTS CHUNK (WHAT) --------
                            ui_elements = item.get("ui_elements", {})
                            if ui_elements:
                                ui_lines = [f"Test ID: {test_id}", "UI Elements:"]
                                for name, el in ui_elements.items():
                                    ui_lines.append(
                                        f"- {name} | role: {el.get('role')} | "
                                        f"purpose: {el.get('purpose')} | "
                                        f"locators: {', '.join(el.get('locator_hints', []))}"
                                    )

                                all_processed_chunks.append(
                                    Document(
                                        page_content="\n".join(ui_lines),
                                        metadata={
                                            "source": file_path.name,
                                            "test_id": test_id,
                                            "section": "ui_elements",
                                            "tags": ",".join(tags)
                                        }
                                    )
                                )

                            # -------- 3. TEST STEPS CHUNK (HOW) --------
                            steps = item.get("test_steps", [])
                            if steps:
                                step_lines = [f"Test ID: {test_id}", "Test Steps:"]
                                for step in steps:
                                    step_lines.append(
                                        f"Step {step.get('step')}: "
                                        f"{step.get('action')} - "
                                        f"{step.get('description', '')} "
                                        f"(target: {step.get('element', step.get('target', ''))})"
                                    )

                                all_processed_chunks.append(
                                    Document(
                                        page_content="\n".join(step_lines),
                                        metadata={
                                            "source": file_path.name,
                                            "test_id": test_id,
                                            "section": "test_steps",
                                            "tags": ",".join(tags)
                                        }
                                    )
                                )

                            # -------- 4. VALIDATION RULES CHUNK (TRUTH) --------
                            validation = item.get("validation_rules", {})
                            if validation:
                                val_lines = [f"Test ID: {test_id}", "Validation Rules:"]
                                for result_type, rules in validation.items():
                                    val_lines.append(f"{result_type.upper()} CONDITIONS:")
                                    for check in rules.get("manual_checks", []):
                                        val_lines.append(f"- Manual check: {check}")
                                    for assertion in rules.get("automation_assertions", []):
                                        val_lines.append(
                                            f"- Assertion: {assertion.get('assertion_type')} | "
                                            f"selector: {assertion.get('selector_hint', '')}"
                                        )

                                all_processed_chunks.append(
                                    Document(
                                        page_content="\n".join(val_lines),
                                        metadata={
                                            "source": file_path.name,
                                            "test_id": test_id,
                                            "section": "validation_rules",
                                            "tags": ",".join(tags)
                                        }
                                    )
                                )

                            # -------- 5. PRE / POST CONDITIONS CHUNK (WHEN / AFTER) --------
                            pre = item.get("preconditions", [])
                            post = item.get("postconditions", [])

                            if pre or post:
                                cond_lines = [f"Test ID: {test_id}"]

                                if pre:
                                    cond_lines.append("Preconditions:")
                                    for p in pre:
                                        cond_lines.append(f"- {p}")

                                if post:
                                    cond_lines.append("Postconditions:")
                                    for p in post:
                                        cond_lines.append(f"- {p}")

                                all_processed_chunks.append(
                                    Document(
                                        page_content="\n".join(cond_lines),
                                        metadata={
                                            "source": file_path.name,
                                            "test_id": test_id,
                                            "section": "conditions",
                                            "tags": ",".join(tags)
                                        }
                                    )
                                )

                            # -------- 6. METADATA / TAGS CHUNK (RETRIEVAL) --------
                            meta_content = (
                                f"Test ID: {test_id}\n"
                                f"Scope: {scope}\n"
                                f"Test Type: {test_type}\n"
                                f"Tags: {', '.join(tags)}"
                            )

                            all_processed_chunks.append(
                                Document(
                                    page_content=meta_content,
                                    metadata={
                                        "source": file_path.name,
                                        "test_id": test_id,
                                        "section": "metadata",
                                        "tags": ",".join(tags)
                                    }
                                )
                            )
                continue # Đã xử lý xong JSON, nhảy sang file tiếp theo

            # ---- XỬ LÝ MD ----
            # if suffix == ".md":
            #     with open(file_path, 'r', encoding='utf-8') as f:
            #         data = f.read()
            #     # 1. Define the headers to split on (Mapping # Flow and ## STEP to metadata)
            #     headers_to_split_on = [("#", "flow_id"), ("##", "test_id")]

            #     md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
            #     md_header_splits = md_splitter.split_text(data)

            #     # 2. Clean up the 'test_id' (Removing 'STEP 1: ' prefix to match BENCHMARK_SUITE)
            #     for doc in md_header_splits:
            #         raw_test_id = doc.metadata.get("test_id", "")
            #         if ":" in raw_test_id:
            #             doc.metadata["test_id"] = raw_test_id.split(":")[-1].strip()
            #         raw_flow_id = doc.metadata.get("flow_id", "")
            #         if ":" in raw_flow_id:
            #             doc.metadata["flow_id"] = raw_flow_id.split(":")[-1].strip()
            #     # Add common metadata
            #     doc.metadata["source"] = file_path.name
            #     all_processed_chunks.extend(splitter.split_documents(md_header_splits))
            #     continue # Đã xử lý xong MD, nhảy sang file tiếp theo

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