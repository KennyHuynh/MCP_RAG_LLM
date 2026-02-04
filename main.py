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
    prompt_router = PromptRouter(llm_client=ai_client, router_prompt_template=prompts["router"], mcp_service=mcp_service)
    user_queries = f'Generate Playwright automation script to complete payment flow'
    # Routing (Classify)
    print(f"\n[User]: {user_queries}")
    routing_info = await prompt_router.get_routing_info(query=user_queries)
    category = routing_info['category']
    print(f"[Router]: Identify user's purpose as -> {category}")
    executor = TaskExecutor(llm_client=ai_client, all_prompts=prompts,
                            mcp_service=mcp_service, rag_storage=storage, routing_info=routing_info)
    response = await executor.execute(
        query=user_queries, 
        routing_info=routing_info
    )
    print(f"[AI's answer]: {response}")

if __name__ == "__main__":
    asyncio.run(run_system())
    
