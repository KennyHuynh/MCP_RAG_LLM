import yaml
import asyncio
from core.llm_client import LLMClient
from core.router import PromptRouter
from infrastructure.database import RAGStorage
from services.mcp_service import MCPService
from core.executor import TaskExecutor
from dotenv import load_dotenv


def load_all_prompts():
    with open("prompts/agent_prompt.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


async def run_system():
    # 1. Initialize instance of classes
    load_dotenv()
    prompts = load_all_prompts()
    storage = RAGStorage()
    mcp_service = MCPService()
    ai_client = LLMClient(model_name="gpt-4o")
    prompt_router = PromptRouter(llm_client=ai_client, router_prompt_template=prompts["router"])
    executor = TaskExecutor(llm_client=ai_client, all_prompts=prompts,
                            mcp_service=mcp_service, rag_storage=storage)

    # 2. Run the process to generate script for a website
    target_url = "https://demo.testarchitect.com/my-account"
    user_queries = [f'Generate Playwright automation code of login feature for: {target_url}']
    print(f"--- Processing page: {target_url} ---")

    for query in user_queries:
        print(f"\n[User]: {query}")
        
        # Step 1: Routing (Classify)
        routing_info = await prompt_router.get_routing_info(query=query)
        category = routing_info['category']
        selected_tools = routing_info['tools']
        print(f"[Router]: Identify user's purpose as -> {category}")
        
        # Step 2: Execution (Execute specific prompt)
        response = await executor.execute(category=category, query=query, selected_tools=selected_tools)
        print(f"[AI's answer]: {response}")


if __name__ == "__main__":
    asyncio.run(run_system())
