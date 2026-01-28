from mcp.server.fastmcp import FastMCP
from playwright.sync_api import sync_playwright

class MCPBrowserService:
    def __init__(self):
        self.mcp = FastMCP("Playwright-Analyzer")

    def get_dom_selectors(self, url: str) -> str:
        """Using Playwright to scan web structure."""
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            # Export ID and name of input and button
            selectors = page.evaluate("""() => 
                Array.from(document.querySelectorAll('input, button'))
                .map(el => ({ tag: el.tagName, id: el.id, name: el.name }))
            """)
            browser.close()
            return f"The structure found at {url}: {selectors}"