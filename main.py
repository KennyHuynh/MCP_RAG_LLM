import yaml
import asyncio
from core.llm_client import LLMClient
from core.router import PromptRouter
from infrastructure.database import RAGStorage
from services.mcp_service import MCPService
from core.executor import TaskExecutor
from dotenv import load_dotenv
import streamlit as st
from infrastructure.data_util import save_uploaded_files


def load_all_prompts():
    with open("prompts/agent_prompt.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


async def run_system(model_name, query, uploaded_files):
    # 1. Initialize instance of classes
    load_dotenv()
    prompts = load_all_prompts()
    save_uploaded_files(uploaded_files)
    storage = RAGStorage()
    mcp_service = MCPService()
    ai_client = LLMClient(model_name=model_name)
    prompt_router = PromptRouter(llm_client=ai_client, router_prompt_template=prompts["router"], mcp_service=mcp_service)
    executor = TaskExecutor(llm_client=ai_client, all_prompts=prompts,
                            mcp_service=mcp_service, rag_storage=storage)

    # # 2. Run the process to generate script for a website
    # target_url = "https://demo.testarchitect.com/my-account"
    # #user_queries = [f'Generate Playwright automation code of login feature for: {target_url}']
    # user_queries = [f'What is login feature?']
    # print(f"--- Processing page: {target_url} ---")

    # for query in user_queries:
    #     print(f"\n[User]: {query}")
        
    # Step 1: Routing (Classify)
    routing_info = await prompt_router.get_routing_info(query=query)
    category = routing_info['category']
    selected_tools = routing_info['tools']
    print(f"[Router]: Identify user's purpose as -> {category}")
        
    # Step 2: Execution (Execute specific prompt)
    response = await executor.execute(category=category, query=query, selected_tools=selected_tools)
    print(f"[AI's answer]: {response}")

    return category, response


# if __name__ == "__main__":
#     asyncio.run(run_system())
# ---------- Streamlit UI ----------
st.set_page_config(page_title="RAG QA Automation Agent", layout="wide")
st.title("🧠 RAG-Powered QA Automation Agent")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Configuration")

    model_name = st.selectbox(
        "Model",
        options=[
            "gpt-4o",
            "gemma3:1b",
        ],
        index=0
    )

    uploaded_files = st.file_uploader(
        "RAG Files",
        type=["json", "yaml", "yml", "md", "txt", "xlsx", "csv"],
        accept_multiple_files=True
    )

# Target URL + Query
target_url = st.text_input(
        "Target URL",
        placeholder="https://example.com/login"
    )

user_query = st.text_area(
        "User Query",
        placeholder="Generate Playwright automation for login",
        height=150
    )

# Submit
if st.button("🚀 Run"):
    if not user_query:
        st.warning("Please enter a user query.")
    else:
        full_query = f"{user_query} {target_url}".strip()

        with st.spinner("Thinking..."):
            category, answer = asyncio.run(
                run_system(
                    model_name=model_name,
                    query=full_query,
                    uploaded_files=uploaded_files
                )
            )

        st.subheader("🧭 Routed As")
        st.code(category)

        st.subheader("🤖 AI Response")
        st.write(answer)