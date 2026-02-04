import asyncio
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
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage, AIMessage
from langgraph.graph.message import add_messages

#Define State Structure
class AgentState(TypedDict):
    # 'add_messages' help append chat history so that AI can remember last steps
    messages: Annotated[List[BaseMessage], add_messages]
    category: str
    tool_trigger_count: int

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
        self.tool_node = ToolNode(self.tools)
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        self.category = routing_info["category"]

    def _check_category(self, state: AgentState):
    # state is passed by LangGraph automatically
        return  state["category"]

    async def _force_rethink_node(self, state: AgentState):
        """
        This node is called when AI wanna end but no MCP tool called yet.
        """
        current_count = state.get("tool_trigger_count", 0)
        return {
            "messages": [HumanMessage(content="It seems no tools are required. You decide to end or check again based on data you have.")],
            "tool_trigger_count": current_count + 1
    }

    def _create_workflow(self):
        graph = StateGraph(AgentState)

        # Define Node (Execution Node)
        graph.add_node("router", self._route_node) # Node for clasifying request into AUTO|MANUAL|GENERAL
        graph.add_node("agent", self._call_model) # Agentic node (using AUTO prompt)
        graph.add_node("action", self._action_node) # Execution node - To execute MCP Tools
        graph.add_node("manual_gen", self._manual_node) # Node for performing Manual/General
        graph.add_node("force_rethink", self._force_rethink_node)

        # Establish entry point(flow) with the first point is router
        graph.set_entry_point("router")
        
        # Conditional Edge: After AI's thoughts, it will call Tool or end flow
        graph.add_conditional_edges(
            "router",
            self._check_category, # Based on category to classify
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
                "force_rethink": "force_rethink",
                "end": END
            }
        )

        # After a tool completes running, back to Agent so that AI can see the result (in Observation) and continue thinking
        graph.add_edge("action", "agent")
        graph.add_edge("force_rethink", "agent")
        graph.add_edge("manual_gen", END)
        return graph
    
    async def _route_node(self, state: AgentState):
        """Using router prompt to classify"""
        query = state["messages"][-1].content
        return {
            "category": state["category"],
            "tool_trigger_count": state.get("tool_trigger_count", 0)
            }

    async def _action_node(self, state: AgentState):
        tool_result = self.tool_node.ainvoke(state)
        return {
            "messages": tool_result["messages"],
        }
    
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
        last_message = messages[-1] # AI's message
        # If AI requests to call Tool (tool_calls), moving forward to node action
        if getattr(last_message, 'tool_calls', []):
            return "continue"
        else:
            if state["tool_trigger_count"] < 2:
                return "force_rethink"
        return "end"
        # else:
        # #total_tool_calls = sum(len(m.tool_calls) for m in messages if isinstance(m, AIMessage) and hasattr(m, 'tool_calls'))
        #     has_tool_observation = any(isinstance(m, ToolMessage) for m in messages)
        #     if state.get("category") == "AUTO" and not has_tool_observation:
        #         if state.get("tool_trigger_count", 0) > 2:
        #         # For AI to back to scan web
        #             return "continue"
        #     if not last_message.content or len(last_message.content) < 4 and not (getattr(last_message, 'tool_calls', [])):
        #         return "force_rethink" # Back to node agent with a note
        #     # If AI returns text only instead tool(name), end flow
        #     return "end"

    
    # Combine RAG info and Observation(data from MCP tools) into one message
    async def _call_model(self, state: AgentState):
        messages = state["messages"]
        # Inject RAG context to the first message if required
        if len(messages) == 1:
            query = messages[-1].content
            rag_context = self.rag_store.search_documents(query)
            # Create System Message to guide Agentic Flow
            combined_prompt = f"{self.prompts['auto']}\n\n{self.prompts['agent_system_message']}"
            system_content = combined_prompt.format(
                context=rag_context if rag_context else "No RAG data.",
                query=query
            )
            messages = [SystemMessage(content=system_content)] + messages
            # system_msg = SystemMessage(content=f"{self.prompts['agent_system_message']}\nContext: {rag_context}")
            # messages = [system_msg] + messages

        # Call LLM's support to call tools
        await asyncio.sleep(1.5)
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
            async for event in self.app.astream(initial_state, config={"recursion_limit": 15}):
                for node_name, output in event.items():
                    print(f"\n[MANAGER]: Node '{node_name}' finished execution.")
                    # Print AI message or Tool's result
                    if "messages" in output:
                        last_msg = output["messages"][-1]
                        print(f"Content: {last_msg.content}...")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error during executing Agent: {str(e)}"

        finally:
            if self.mcp_service and hasattr(self.mcp_service, 'web_automation_service'):
                await self.mcp_service.web_automation_service.cleanup()
                print("Ending...")
