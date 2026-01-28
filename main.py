import asyncio
from infrastructure.database import RAGStorage
from services.mcp_service import MCPBrowserService
from core.agent_engine import GenerationEngine

async def run_system():
    # 1. Initialize instance of classes
    storage = RAGStorage()
    browser_service = MCPBrowserService()
    engine = GenerationEngine(browser_service, storage)

    # 2. Run the process to generate script for a website
    target_url = "https://demo.testarchitect.com/my-account"
    print(f"--- Processing page: {target_url} ---")
    
    final_code = await engine.execute(target_url)
    
    print("\n" + "="*50)
    print("FINAL PLAYWRIGHT GENERATED FROM RAG + MCP + OLLAMA:")
    print("="*50)
    print(final_code)

if __name__ == "__main__":
    asyncio.run(run_system())