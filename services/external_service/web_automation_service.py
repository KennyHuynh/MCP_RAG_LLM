import json
import re
from pydantic import BaseModel, Field
from typing import Optional
from playwright.async_api import async_playwright

class WebScannerInput(BaseModel):
    """This class is identifying input data structure for tool get_dom_selectors"""
    query: str = Field(description="User's query contains URL needs to be scanned/got.")
    url_override: Optional[str] = Field(default=None, description="The specific URL if existing.")


class WebAutomationService:

    async def get_dom_selectors(self, query: str) -> str:
        """Using Playwright to scan web structure.
        Export url from user query"""
        urls = re.findall(r'https?://[^\s]+', query)
        url = urls[0] if urls else "https://google.com"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent="MCP-Automation-Bot/1.0"
            )
            page = await context.new_page()
            try:
                # Wait until page loaded (timeout 30s)
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Script JS to get Selectors for Playwright
                # just get interactionable Selectors to avoid AI be noise.
                selectors = await page.evaluate("""() => {
                    const elements = document.querySelectorAll('input, button, a, select, textarea');
                    return Array.from(elements).map(el => ({
                        tag: el.tagName.toLowerCase(),
                        id: el.id || null,
                        name: el.getAttribute('name') || null,
                        placeholder: el.getAttribute('placeholder') || null,
                        aria_label: el.getAttribute('aria-label') || null,
                        text: el.innerText.trim().substring(0, 30) || null
                    })).filter(el => el.id || el.name || el.aria_label || el.text);
                }""")

                await browser.close()

                # Return result as JSON so that AI can easily resolve in Prompt
                return json.dumps({
                    "url": url,
                    "elements_found": len(selectors),
                    # limit 50 elements to avoid waste of using Token
                    "selectors": selectors[:50]
                }, indent=2, ensure_ascii=False)

            except Exception as e:
                await browser.close()
                return f"❌ Error when accessing website {url}: {str(e)}"
