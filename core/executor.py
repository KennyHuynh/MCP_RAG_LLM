from langchain_ollama import ChatOllama
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_classic.agents import create_react_agent
from langchain_classic.agents import AgentExecutor
from langchain_classic.agents.output_parsers import ReActSingleInputOutputParser

from core.llm_client import LLMClient
from infrastructure.database import RAGStorage
from services.mcp_service import MCPService
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import Annotated, List, TypedDict, Union
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages

#Define State Structure
class AgentState(TypedDict):
    # 'add_messages' help append chat history so that AI can remember last steps
    messages: Annotated[List[BaseMessage], add_messages]
    category: str

class TaskExecutor:
    def __init__(self, llm_client:LLMClient, all_prompts:dict, mcp_service:MCPService, rag_storage:RAGStorage, routing_info):
        # self.llm = ChatOllama(
        #     model="llama3.2:3b", 
        #     temperature=0
        #     )
        self.llm = llm_client
        self.rag_store = rag_storage
        self.mcp_service = mcp_service
        self.prompts = all_prompts
        self.tools = [
            val["instance"] for val in self.mcp_service.tools.values()
        ]
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        self.category = routing_info["category"]
    
    def _create_workflow(self):
        graph = StateGraph(AgentState)

        # Define Node (Execution Node)
        graph.add_node("router", self._route_node) # Node for clasifying request into AUTO|MANUAL|GENERAL
        graph.add_node("agent", self._call_model) # Agentic node (using AUTO prompt)
        graph.add_node("action", ToolNode(self.tools)) # Execution node - To execute MCP Tools
        graph.add_node("manual_gen", self._manual_node) # Node for performing Manual/General

        # Establish entry point(flow) with the first point is router
        graph.set_entry_point("router")
        
        # Conditional Edge: After AI's thoughts, it will call Tool or end flow
        graph.add_conditional_edges(
            "router",
            lambda state: state["category"], # Based on category to classify
            {
                "AUTO": "agent",
                "MANUAL": "manual_gen",
                "GENERAL": "manual_gen"
            }
        )
        graph.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "action",
                "end": END
            }
        )

        # After a tool completes running, back to Agent so that AI can see the result (in Observation) and continue thinking
        graph.add_edge("action", "agent")
        graph.add_edge("manual_gen", END)
        return graph
    
    async def _route_node(self, state: AgentState):
        """Using router prompt to classify"""
        query = state["messages"][-1].content
        # Call call_with_json hoặc get_structured_output để phân loại
        return {"category": self.category}
    
    async def _manual_node(self, state: AgentState):
        """Using manual/general prompt"""
        query = state["messages"][-1].content
        category = state["category"].lower() # manual or general
        context = self.rag_store.search_documents(query)
        prompt = self.prompts[category].format(context=context, query=query)
        response = await self.llm.call_ai(prompt)
        return {"messages": [HumanMessage(content=response)]}
    
    def _should_continue(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        # If AI requests to call Tool (tool_calls), moving forward to node action
        if last_message.tool_calls:
            return "continue"
        if not last_message.content or len(last_message.content) < 5:
            return "continue" # Back to node agent with a note
        # If AI returns text only instead tool(name), end flow
        return "end"
    
    # Combine RAG info and Observation(data from MCP tools) into one message
    async def _call_model(self, state: AgentState):
        messages = state["messages"]
        # Inject RAG context to the first message if required
        if len(messages) == 1:
            query = messages[-1].content
            rag_context = self.rag_store.search_documents(query)
            # Create System Message to guide Agentic Flow
            system_msg = SystemMessage(content=f"{self.prompts['agent_system_message']}\nContext: {rag_context}")
            messages = [system_msg] + messages

        # Call LLM's support to call tools
        response = await self.llm.llm.bind_tools(self.tools).ainvoke(messages)
        print(f"--- [AI Thought]: {response.content} ---") # CHeck if AI still want to call next tool
        print(f"--- [Tool Calls]: {response.tool_calls} ---")
        return {"messages": [response]}

    async def execute(self, query: str, routing_info: dict):
        try:
            """
            RAG Chain process: 
            1. Get category and selected tools from Router
            2. Invoke data from RAGStore
            3. Combine into Prompt and call LLM
            """
            initial_state = {
                "messages": [HumanMessage(content=query)],
                "category": routing_info["category"]
            }

            #THIS BLOCK is used for logic to search tool, inject additional context to prompt MANUALLY. ALL WILL AUTOMATICALLY PROCESS VIA EDGEs and NODEs
            # category = routing_info['category']
            # selected_tools = routing_info['tools']
            # tool_params = routing_info.get("tool_params", {})
            # # IMPORTANT. Always ensure original query is in params so that tool can find URL
            # tool_params["query"] = query
            
            # rag_context = ""
            # if category != 'GENERAL':
            #     rag_context = self.rag_store.search_documents(query)
            
            # mcp_context = ""
            # # If Router cannot specify tool, use logic to automatically scan keyword in class MCPService
            # if selected_tools is None:
            #     selected_tools = [
            #         name for name, info in self.mcp_service.tools.items()
            #         if any(kw in query.lower() for kw in info.get('keywords', []))
            #     ]
            
            # # Execute selected tool via MCP Service
            # for tool_name in selected_tools:
            #     if isinstance(tool_name, dict):
            #         tool_name = tool_name.get("name") or tool_name.get("tool") or list(tool_name.values())[0]
            #     else:
            #         # If AI return the correct format
            #         tool_name = tool_name
            #     # Call tool and insert result to context (context)
            #     tool_result = await self.mcp_service.call_tool_async(tool_name, query=tool_params["query"])
            #     mcp_context += f"\n[Data from {tool_name}]: {tool_result}"
            
            # full_context = f"{rag_context}\n{mcp_context}".strip()

            # prompt_template = self.prompts.get(category.lower(), self.prompts['general'])
            # # final_prompt = f"""
            # # Internal knowledge context:
            # # -------------------------
            # # {rag_context_docs}
            # # -------------------------
            
            # # Based on the above context, perform following request:
            # # {prompt_template.format(query=query)}
            
            # # Note: If information doesn't exist in context, just answer based on your knowledge with detailed notes.
            # # """
            # final_prompt = prompt_template.format(
            #     context = full_context if full_context else "No additional context.",
            #     query = query
            # )
            try:
                # # Run grapth with limitation (recursion_limit) to save resources
                # # Increase to 15 steps to proceed complex business
                # config = {"recursion_limit": 5}
                # final_state = await self.app.ainvoke(initial_state, config=config)
            
                # # Return the last message Asnwer of AI)
                # return final_state["messages"][-1].content

                async for event in self.app.astream(initial_state, config={"recursion_limit": 15}):
                    for node_name, output in event.items():
                        print(f"\n[MANAGER]: Node '{node_name}' finished execution.")
                        # Print AI message or Tool's result
                        if "messages" in output:
                            last_msg = output["messages"][-1]
                            print(f"Content: {last_msg.content[:100]}...") 
            
            except Exception as e:
                return f"❌ Error during executing Agent: {str(e)}"
        finally:
            if self.mcp_service and hasattr(self.mcp_service, 'web_automation_service'):
                await self.mcp_service.web_automation_service.cleanup()
                print("Ending...")
