from langchain_ollama import ChatOllama
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_classic.agents import create_react_agent
from langchain_classic.agents import AgentExecutor
from langchain_classic.agents.output_parsers import ReActSingleInputOutputParser

from core.llm_client import LLMClient
from infrastructure.database import RAGStorage
from services.mcp_service import MCPService
# from langgraph.prebuilt import create_react_agent, chat_agent_executor


class TaskExecutor:
    def __init__(self, llm_client:LLMClient, all_prompts:dict, mcp_service:MCPService, rag_storage:RAGStorage):
        # self.llm = ChatOllama(
        #     model="llama3.2:3b", 
        #     temperature=0
        #     )
        self.llm = llm_client
        self.rag_store = rag_storage
        self.mcp_service = mcp_service
        # self.tools = [
        #     Tool(
        #         name="ScanWebLayout",
        #         func=mcp_service.get_dom_selectors,
        #         description="Scan web page to get selectors. DO NOT include 'url=' or quotes inside the input."
        #     ),
        #     Tool(
        #         name="GetCodeBestPractices",
        #         func=lambda q: str(self.rag_storage.search_documents(q)),
        #         description=("Retrieve the most only ONE relevant Playwright best practice."
        # "Each result is separated by '--- NEXT BEST PRACTICE ---'. ")
        #     )
        # ]
        
        self.prompts = all_prompts
        #self.agent = self._build_agent()

    def _build_agent(self):
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompts,
            output_parser=ReActSingleInputOutputParser())

        self.executor = AgentExecutor(
            agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    async def execute(self, category: str, query: str, selected_tools: list = None):
        """
        RAG Chain process: 
        1. Get category and selected tools from Router
        2. Invoke data from RAGStore
        3. Combine into Prompt and call LLM
        """
        rag_context = ""
        if category != 'GENERAL':
            rag_context = self.rag_store.search_documents(query)
        
        mcp_context = ""
        # If Router cannot specify tool, use logic to automatically scan keyword in class MCPService
        if selected_tools is None:
            selected_tools = [
                name for name, info in self.mcp_service.tools.items()
                if any(kw in query.lower() for kw in info.get('keywords', []))
            ]
        
        # Execute selected tool via MCP Service
        for tool_name in selected_tools:
            # Call tool and insert result to context (context)
            tool_result = await self.mcp_service.call_tool_async(tool_name, query=query)
            mcp_context += f"\n[Data from {tool_name}]: {tool_result}"
        
        full_context = f"{rag_context}\n{mcp_context}".strip()

        prompt_template = self.prompts.get(category.lower(), self.prompts['general'])
        # final_prompt = f"""
        # Internal knowledge context:
        # -------------------------
        # {rag_context_docs}
        # -------------------------
        
        # Based on the above context, perform following request:
        # {prompt_template.format(query=query)}
        
        # Note: If information doesn't exist in context, just answer based on your knowledge with detailed notes.
        # """
        final_prompt = prompt_template.format(
            context = full_context if full_context else "No additional context.",
            query = query
        )
        response = await self.llm.call_ai(final_prompt)
        return response
