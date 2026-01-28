import re
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

class MCPService:
    def __init__(self):
        self.mcp = FastMCP("Playwright-Analyzer")
        self.tools = {
            "web_element_tool": {
                "func": self._get_dom_selectors,
                "keywords": ["scan", "automation", "web"],
                "desc": "To get and export all element of an URL."
            }
        }

    # IDENTIFY METHODS THAT TASKEXECUTOR CALLING
    async def call_tool_async(self, tool_name: str, query: str):
        """Execute tool asynchronize"""
        if tool_name in self.tools:
            print(f"--- [MCP] Executing tool: {tool_name} ---")
            # Call relevant method (giả định là async)
            return await self.tools[tool_name]["func"](query)
        return f"Error: Not found tool '{tool_name}'."

    def call_tool(self, tool_name: str, query: str):
        """Execute tool synchronize (If not using await)"""
        if tool_name in self.tools:
            return f"[Data from tool: {tool_name}]"
        return "Tool not found."

    async def _get_dom_selectors(self, query: str) -> str:
        """Using Playwright to scan web structure.
        Export url from user query"""
        urls = re.findall(r'https?://[^\s]+', query)
        url = urls[0] if urls else "https://google.com"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            # Export ID and name of input and button
            selectors = await page.evaluate("""() => 
                Array.from(document.querySelectorAll('input, button'))
                .map(el => ({ tag: el.tagName, id: el.id, name: el.name }))
            """)
            await browser.close()
            return f"The structure found at {url}: {selectors}"