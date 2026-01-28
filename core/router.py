from core.llm_client import LLMClient
import json


class PromptRouter:
    def __init__(self, llm_client: LLMClient, router_prompt_template: str):
        self.llm = llm_client
        self.template = router_prompt_template

    async def get_category(self, user_query: str) -> str:
        relevant_prompt = f"{self.template.format(query=user_query)}\n return JSON: {{\"category\": \"AUTO|MANUAL|GENERAL\"}}"
        raw_json = await self.llm.call_with_json(relevant_prompt)
        return json.loads(raw_json).get("category", "GENERAL").upper()

    async def get_routing_info(self, query: str) -> dict:
        prompt = f"""Classify: {query}.
            Available Tools: web_element_tool.
            Return JSON: {{"category": "...", "tools": ["name1", "name2"]}}"""
        # Ask LLM return the required tool
        raw_json = await self.llm.call_with_json(prompt)
        try:
            data = json.loads(raw_json) # raw_json is now string because of the above await.
            return {
            "category": data.get("category", "GENERAL").upper(),
            "tools": data.get("tools", [])
        }
        except Exception as e:
            return {"category": "GENERAL", "tools": []}
    