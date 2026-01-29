import json
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
from langchain_core.tools import StructuredTool

from services.external_service.web_automation_service import WebAutomationService, WebScannerInput


class MCPService:
    def __init__(self):
        self.mcp = FastMCP("MCP-Adapter")
        self.web_automation_service = WebAutomationService()

        scanner_tool_obj = StructuredTool.from_function(
                name="mcp_web_element_tool",
                coroutine=self.web_automation_service.get_dom_selectors,
                args_schema=WebScannerInput,
                description="To get and export all element of an website by URL."
            )

        self.tools = {
            "mcp_web_element_tool": {
                "instance": scanner_tool_obj,
                "func": self.web_automation_service.get_dom_selectors, # Tham chiếu hàm để gọi ["func"]
                "desc": scanner_tool_obj.description
            }
        }
        #self._setup_mcp_tools()

# This method is used if MCP is running as standalone server so that other add-ons such as ClaudeDesktop, Cusor or external agent AI can connect to.
    # def _setup_mcp_tools(self):
    #     """Register defnition as Model Context Protocol"""
    #     for name, info in self.tools.items():
    #         self.mcp.tool(name=name, description=info["desc"])(info["func"])

    # IDENTIFY METHODS THAT TASKEXECUTOR CALLING
    async def call_tool_async(self, tool_name: str, query: str):
        """Execute tool asynchronize"""
        if isinstance(tool_name, dict):
            tool_name = tool_name.get("name") or list(tool_name.values())[0]

        if tool_name in self.tools:
            print(f"--- [MCP] Executing tool: {tool_name} ---")
            # Call relevant method (giả định là async)
            result_data = await self.tools[tool_name]["func"](query=query)
            return json.dumps(result_data, indent=2, ensure_ascii=False)
        return f"Error: Not found tool '{tool_name}'."

    def call_tool(self, tool_name: str, query: str):
        """Execute tool synchronize (If not using await)"""
        if tool_name in self.tools:
            return f"[Data from tool: {tool_name}]"
        return "Tool not found."
