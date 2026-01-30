import asyncio
import json
import re
from pydantic import BaseModel, Field
from typing import Optional
from playwright.async_api import async_playwright


class WebScannerInput(BaseModel):
    """This class is identifying input data structure for tool get_dom_selectors"""
    query: str = Field(description="User wants to scan web elements.")
    action: Optional[str] = Field(default=None, description="Required action(click/fill) to go to next step. Info is retrieve from RAG.")
    target: Optional[str] = Field(default=None, description="Target Selector for action. Info is retrieve from RAG.")


# class LoginInput(BaseModel):
#     query: str = Field(
#         description="User wants to generate script for Login feature")
#     url: str = Field(description="Login page url")
#     username_selector: str = Field(
#         description="Selector of username input (id, css, xpath)")
#     password_selector: str = Field(description="Selector of password input")
#     submit_selector: str = Field(description="Selector of Login button")


# class PaymentInput(BaseModel):
#     query: str = Field(
#         description="User wants to generate script for Checkout/Payment feature")
#     item_name: str = Field(description="Name of item need to checkout")
#     payment_method: str = Field(
#         description="Payment method: 'visa', 'momo', 'bank_transfer'")


class WebAutomationService:
    def __init__(self):
        self.browser = None
        self.page = None

    async def get_dom_selectors(self, query: str, action: str = None, target: str= None, value: str = None) -> str:
        """Using Playwright to scan web structure.
        Export url from user query"""
        url = re.findall(r'https?://[^\s]+', query)[0]
        if not self.browser:
            p = await async_playwright().start()
            self.browser = await p.chromium.launch(headless=True)
            context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent="MCP-Automation-Bot/1.0"
            )
            self.page = await context.new_page()

        try:
            # Wait until page loaded (timeout 30s)
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            if url:
                await self.page.goto(url, wait_until="networkidle")
            elif action == "click" and target:
                await self.page.click(target)
                await self.page.wait_for_load_state("networkidle")
            elif action == "fill" and target:
                await self.page.fill(target, value)

            # Script JS to get Selectors for Playwright
            # just get interactionable Selectors to avoid AI be noise.
            selectors = await self.page.evaluate("""() => {
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

            # Return result as JSON so that AI can easily resolve in Prompt
            return json.dumps({
                "url": url,
                "elements_found": len(selectors),
                # limit 50 elements to avoid waste of using Token
                "selectors": selectors[:50]
            }, indent=2, ensure_ascii=False)

        except Exception as e:
            await self.browser.close()
            return f"❌ Error when accessing website {url}: {str(e)}"
            

    # async def generate_login_script(self, query: str, url: str, username_selector: str, password_selector: str, submit_selector: str) -> str:
    #     script = f"""
    #     // Playwright Login Script
    #     await page.goto('{url}');
    #     await page.fill('{username_selector}', 'YOUR_USERNAME');
    #     await page.fill('{password_selector}', 'YOUR_PASSWORD');
    #     await page.click('{submit_selector}');
    #     await expect(page).not.toHaveURL(/.*login/);
    #     """
    #     return script.strip()
    
    async def cleanup(self):
        if not self.browser:
            return
    
    # Shield giúp bảo vệ quá trình đóng không bị hủy bởi loop termination
        async def _close():
            try:
                if self.page: await self.page.close()
                if self.browser: await self.browser.close()
                if self._playwright: await self._playwright.stop()
            except: pass
            finally:
                self.page = None
                self.browser = None
                self._playwright = None

        await asyncio.shield(_close())
    
