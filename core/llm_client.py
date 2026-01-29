import os
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage


class LLMClient:
    def __init__(self, model_name="gpt-4o"):
        self.model_name = model_name
        if "openai" or "gpt" in self._model_name:
            self.llm = ChatOpenAI(
                model=self.model_name,
                api_key=os.environ.get("OPEN_API_KEY"),
                base_url="https://models.inference.ai.azure.com",
                temperature=0
            )
        else:
            self.llm = ChatOllama(
                model=self.model_name,
                temperature=0
            )

    async def call_ai(self, prompt: str, temperature: float = 0.3) -> str:
        print(f"--- [Log] Calling Model: {self.model_name} ---")
        try:
            # Send message and receive BaseMessage object
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            return f"Error when calling OpenAI: {str(e)}"

    async def call_with_json(self, prompt: str):
        try:
            json_model = self.llm.bind(response_format={"type": "json_object"})
            response = await json_model.ainvoke([
                SystemMessage(
                    content="Your are an assistant just returns data as JSON format."),
                HumanMessage(content=prompt)
            ])
            return response.content
        except Exception as e:
            print(f"JSON API error: {e}")
            return '{"category": "GENERAL", "tools": []}'

    async def get_structured_output(self, schema: str, prompt: str):
         """
        Force AI return correct format Dictionary/Object.
        This is wrapper method of with_structured_output of LangChain.
        """
         try:
            # Init a model that convert to Schema
            # LangChain will automatically handle JSON Mode and Validation
            structured_llm = self.llm.with_structured_output(schema)

            # Execute and return result parsed to Python Dict
            result = await structured_llm.ainvoke(prompt)
            return result
         except Exception as e:
            print(f"--- [LLM Error] Error structure identifying: {e} ---")
            return None
