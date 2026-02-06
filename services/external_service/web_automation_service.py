import asyncio
from enum import Enum
import json
import re
from pydantic import BaseModel, Field
from typing import Optional, Union
from playwright.async_api import async_playwright
from rapidfuzz import fuzz


class LocatorType(Enum):
    BUTTON = "button"
    TEXTBOX = "textbox"
    LABEL = "label"
    PLACEHOLDER = "placeholder"
    ROLE = "role"
    INPUT = "input"
    LINK = "a"
    ANY = "any"


class WebScannerInput(BaseModel):
    """This class is identifying input data structure for tool get_dom_selectors"""
    action: Optional[Union[str, dict]] = Field(
        default=None, description="Required action(click/fill) to go to next step. Info is retrieved from RAG.")
    target: Optional[Union[str, dict]] = Field(
        default=None, description="Target Selector for action. Info is retrieved exactly from RAG.")
    value: Optional[str] = Field(
        None, description="The value to be filled if action is 'fill.'")
    url_override: Optional[str] = Field(
        None, description="The specific URL that AI privately exports from RAG or User's query in http or https format. Never invent, guess, or use placeholder values like 'laptop' or '16gb-ram'")


class WebAutomationService:
    def __init__(self):
        self._playwright = None
        self.browser = None
        self.page = None
        self._lock = asyncio.Lock()

    async def _ensure_browser(self):
        """Init brower (Singleton)"""
        async with self._lock:
            if not self.browser:
                self._playwright = await async_playwright().start()
                self.browser = await self._playwright.chromium.launch(
                    headless=False,
                    slow_mo=1000)
                self.context = await self.browser.new_context(
                    ignore_https_errors=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
                )
                self.page = await self.context.new_page()
                print(f"Service ID: {id(self)}")

    async def get_dom_selectors(self, action: str = None, target: any = None, value: str = None, url_override: str = None) -> str:
        async with self._lock:
            await self._internal_ensure_browser()
            actual_target = target
            target_type = "any"
            target_element = None
            actual_url = self.page.url if self.page else url_override
            try:
                if url_override and (url_override not in actual_url):
                    # If having a new URL, navigate to this new one
                    await self.page.goto(url_override)
                    await self.page.wait_for_load_state("networkidle")
                actual_url = self.page.url
                if target:
                    for locator_type in LocatorType:
                        if locator_type.name.lower() in target:
                            target_type = locator_type.value
                            break
                    if target_type == LocatorType.LINK:
                        actual_target = "".join(self._parse_target(
                            target=target).rsplit(target_type, 1))
                    else:
                        actual_target = self._parse_target(
                            target=target).split(target_type)[0].strip()

                    target_element, meta_data = await self._scan_current_page(actual_target, target_type)

                    if isinstance(action, dict):
                        action = action["description"]
                    target_element_count = await target_element.count() if target_element else 0
                    if target_element_count == 1:
                        if action and actual_target:
                            # Check if target exist at the current page
                            if target_element:
                                if await target_element.is_visible(timeout=5000):
                                    try:
                                        if action == "click":
                                            await target_element.click()
                                            await self.page.wait_for_load_state("networkidle", timeout=5000)
                                        elif action == "fill":
                                            await target_element.fill(str(value))
                                            await self.page.wait_for_timeout(1000)
                                        elif action == "select":
                                            await target_element.select_option(str(value))
                                            await self.page.wait_for_timeout(1000)
                                        actual_url = self.page.url
                                        await self.page.wait_for_timeout(1000)
                                    except Exception as e:
                                        return f"⚠️ The selector '{actual_target}' found but unable to perform {action}. Error: {str(e)}"
                                else:
                                    return json.dumps({
                                        "error": f"Selector from RAG '{actual_target}' not visible at the current page.",
                                        "url": actual_url,
                                    }, ensure_ascii=False)
                    else:
                        return json.dumps({
                            "error": f"Selector from RAG '{actual_target}'not found at the current page. You decide a locator with text approximately matches with value '{actual_target}'",
                            "url": actual_url,
                            "meta_data": meta_data
                        }, indent=2, ensure_ascii=False)
            except Exception as e:
                if "net::ERR_ABORTED" in str(e):
                    print(
                        f"--- [System] Error ERR_ABORTED at {actual_url}, trying... ---")
                    await asyncio.sleep(1)
                    try:
                        await self.page.goto(actual_url, wait_until="load", timeout=20000)
                        return await self.get_dom_selectors(url_override=actual_url)
                    except:
                        return f"❌ Error: Unable to load {actual_url} after retry."
                else:
                    return json.dumps({
                        "error": f"Unable to interact with alternative selector for {actual_target} from available selectors. No need to repeat.",
                        "url": actual_url,
                        "meta_data": meta_data
                    }, indent=2, ensure_ascii=False)

    async def _internal_ensure_browser(self):
        if not self.browser:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(headless=False)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"
            )
            self.page = await self.context.new_page()

    async def _scan_current_page(self, search_text: str = None, suggested_target_type: str = "any") -> list:
        found_flag = False
        results = []
        if not self.page:
            return []

        try:
            if search_text:
                base_locator = self.page.get_by_text(search_text, exact=False)
            count = await base_locator.count()
            if(count == 1):
                single_metadata = await base_locator.evaluate("""(node) => {
                        return {
                            tag: node.tagName.toLowerCase(),
                            id: node.id || null,
                            name: node.getAttribute('name') || null,
                            placeholder: node.getAttribute('placeholder') || node.placeholder || null,
                            role: node.getAttribute('role') || null,
                            // textContent can get complex text that innerText can miss
                            text: (node.textContent || "").replace(/\\s+/g, ' ').trim().substring(0, 50),
                            type: node.getAttribute('type') || null
                        };
                    }""")
                results.append(single_metadata)
                for m in single_metadata.values():
                    if suggested_target_type == m:
                        return base_locator, results

            if count < 1 or found_flag == False:
                base_locator = self.page.locator("button, input, select, textarea, a")
                count = await base_locator.count()

            for i in range(min(count, 200)):
                el = base_locator.nth(i)
                if await el.is_visible():
                    metadata = await el.evaluate("""(node) => {
                        return {
                            tag: node.tagName.toLowerCase(),
                            id: node.id || null,
                            name: node.getAttribute('name') || null,
                            placeholder: node.getAttribute('placeholder') || node.placeholder || null,
                            role: node.getAttribute('role') || null,
                            // textContent can get complex text that innerText can miss
                            text: (node.textContent || "").replace(/\\s+/g, ' ').trim().substring(0, 50),
                            type: node.getAttribute('type') || null
                        };
                    }""")
                    metadata["playwright_hint"] = f"get_by_text('{metadata['text']}')" if metadata[
                        'text'] else f"locator('{metadata['tag']}')"
                    vals = [str(v).lower()
                            for v in metadata.values() if v is not None]
                    if (match := next((v for v in vals if v.lower() == suggested_target_type.lower()), None)) and \
                            (fuzz_match := next((v for v in vals if fuzz.ratio(v.lower(), search_text.lower()) > 50), None)):
                        print(
                            f"ratio is: {fuzz.ratio(fuzz_match.lower(), search_text.lower())}")
                        selector = el
                        results.append(metadata)
                        return selector, results
            return None, []
        except Exception as e:
            print(f"--- [Hybrid Scan Error] {str(e)} ---")
            return []

    def _parse_target(self, target: any) -> str:
        if not target:
            return ""

        if isinstance(target, dict):
            parsed = target.get("value") or \
                target.get("selector") or \
                target.get("id") or \
                target.get("description")

            if not parsed:
                values = list(target.values())
                parsed = values[0] if values else ""
            return str(parsed)

        elif isinstance(target, list):
            return str(target[0]) if target else ""

        elif isinstance(target, str):
            target_str = str(target).strip()
            if "has-text" in target_str and "'" not in target_str and '"' not in target_str:
                target_str = re.sub(r'has-text\((.*?)\)',
                                    r"has-text('\1')", target_str)
            return target_str

    async def cleanup(self):
        async with self._lock:
            if not self.browser:
                return

        # Shield help protect browser close not aborted by loop
            async def _close():
                try:
                    if self.page:
                        await self.page.close()
                    if self.browser:
                        await self.browser.close()
                    if self._playwright:
                        await self._playwright.stop()
                except:
                    pass
                finally:
                    self.page = None
                    self.browser = None
                    self._playwright = None

            await asyncio.shield(_close())
