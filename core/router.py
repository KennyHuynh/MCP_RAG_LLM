from core.llm_client import LLMClient
import json

from services.mcp_service import MCPService


class PromptRouter:
    def __init__(self, llm_client: LLMClient, router_prompt_template: str, mcp_service: MCPService):
        self.llm = llm_client
        self.template = router_prompt_template
        self.mcp_service = mcp_service

    async def get_routing_info(self, query: str) -> dict:
        tools_metadata = []
        if self.mcp_service and hasattr(self.mcp_service, 'tools'):
            for name, tool_obj in self.mcp_service.tools.items():
                tool_instance = tool_obj["instance"]
                description = tool_instance.description
                try:
                    arg_schema = tool_instance.args_schema.model_json_schema() if tool_instance.args_schema else {}
                except AttributeError:
                    arg_schema = tool_instance.args_schema.schema()

                tools_metadata.append(
                    {
                        "name": name,
                        "description": description,
                        "required_params": arg_schema.get("required", []),
                        "param_details": arg_schema.get("properties", {})
                    }
                )

        prompt = f"""
            AVAILABLE MCP TOOLS AND PARAMETER:
            {json.dumps(tools_metadata, indent=2, ensure_ascii=False)}
            Classify: {query} into: AUTO, MANUAL OR GENERAL.
            If category is MANUAL OR GENERAL, no need to use MCP tools.
            Return JSON:
            {{
                "category": "AUTO | MANUAL | GENERAL",
                "tools": [{{ "name": "name", "args": {{ "argument": "value" }} }}]
            }}
            """
        route_schema = {
            "title": "RoutingDecision",  # must have for with_structure_tool method
            # must have for with_structure_tool method
            "description": "Classify user's intent and select proper tools",
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": ["AUTO", "MANUAL", "GENERAL"]},
                "tools": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "args": {"type": "object"}
                        }
                    }
                }
            },
            "required": ["category", "tools"]
        }
        # Ask LLM return the required tool
        # raw_json = await self.llm.call_with_json(prompt)
        # try:
        #     # raw_json is now string because of the above await.
        #     data = json.loads(raw_json)
        #     return {
        #         "category": data.get("category", "GENERAL").upper(),
        #         "tools": data.get("tools", [])
        #     }
        # except Exception as e:
        #     return {"category": "GENERAL", "tools": []}
        data = await self.llm.get_structured_output(schema=route_schema, prompt=prompt)

        return data or {"category": "GENERAL", "tools": []}

