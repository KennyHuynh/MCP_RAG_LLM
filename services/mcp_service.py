import json
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
from langchain_core.tools import StructuredTool

from services.external_service.web_automation_service import WebAutomationService, WebScannerInput


class MCPService:
    def __init__(self):
        self.mcp = FastMCP("MCP-Adapter")
        self.web_automation_service = WebAutomationService()

        scan_web_tool_obj = StructuredTool.from_function(
                name="mcp_scan_web_tool",
                coroutine=self.web_automation_service.get_dom_selectors,
                args_schema=WebScannerInput,
                description="Automation Tool. If tool doesn't provide required information, USE data in RAG."
            )
        
        # gen_login_tool_obj = StructuredTool.from_function(
        #         name="mcp_gen_login_tool",
        #         coroutine=self.web_automation_service.generate_login_script,
        #         args_schema=LoginInput,
        #         description="This is for testing purpose"
        #     )

        self.tools = {
            "mcp_scan_web_tool": {
                "instance": scan_web_tool_obj,
                "func": self.web_automation_service.get_dom_selectors, # Reference the function to call ["func"]
                "desc": scan_web_tool_obj.description
            }
            # ,
            # "mcp_gen_login_tool": {
            #     "instance": gen_login_tool_obj,
            #     "func": self.web_automation_service.generate_login_script, # Reference the function to call ["func"]
            #     "desc": gen_login_tool_obj.description
            # }
        }
        #self._setup_mcp_tools()

# This method is used if MCP is running as standalone server so that other add-ons such as ClaudeDesktop, Cusor or external agent AI can connect to.
    # def _setup_mcp_tools(self):
    #     """Register defnition as Model Context Protocol"""
    #     for name, info in self.tools.items():
    #         self.mcp.tool(name=name, description=info["desc"])(info["func"])

    # IDENTIFY METHODS THAT TASKEXECUTOR CALLING
    async def call_tool_async(self, tool_raw: str, query: str):
        """Execute tool asynchronize"""
        if isinstance(tool_raw, dict):
            values = list(tool_raw.values())
            tool_name = tool_name.get("name") or (values(0) if values else None)
        if not tool_name:
            return "Cannot identify tool to execute"
        if tool_name in self.tools:
            print(f"--- [MCP] Executing tool: {tool_name} ---")
            # Call relevant method (assumption is async)
            result_data = await self.tools[tool_name]["func"](query=query)
            return json.dumps(result_data, indent=2, ensure_ascii=False)
        return f"Error: Not found tool '{tool_name}'."

    def call_tool(self, tool_name: str, query: str):
        """Execute tool synchronize (If not using await)"""
        if tool_name in self.tools:
            return f"[Data from tool: {tool_name}]"
        return "Tool not found."

