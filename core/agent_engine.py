from langchain_ollama import ChatOllama
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_classic.agents import create_react_agent
from langchain_classic.agents import AgentExecutor
from langchain_classic.agents.output_parsers import ReActSingleInputOutputParser
# from langgraph.prebuilt import create_react_agent, chat_agent_executor


class GenerationEngine:
    def __init__(self, browser_service, rag_storage):
        self.llm = ChatOllama(
            model="llama3.2:3b", 
            temperature=0
            )
        self.tools = [
            Tool(
                name="ScanWebLayout",
                func=browser_service.get_dom_selectors,
                description="Scan web page to get selectors. DO NOT include 'url=' or quotes inside the input."
            ),
            Tool(
                name="GetCodeBestPractices",
                func=lambda q: str(rag_storage.search_templates(q)),
                description=("Retrieve the most only ONE relevant Playwright best practice."
        "Each result is separated by '--- NEXT BEST PRACTICE ---'. ")
            )
        ]
        self.agent = self._build_agent()

    def _build_agent(self):

        # template = """You are a QA Engineer. Resolve the request using the available tools.
        # Tools: {tools}
        # Mandatory Format:
        # Thought: Your reasoning process.
        # Action: Tool name (must be one of [{tool_names}]).
        # Action Input: Parameters for the tool.
        # Observation: The returned result.
        # ... (Repeat if necessary)
        # Strict Operational Rules:
        #  1. No Repetition: Do not perform the exact same Action with the exact same Action Input more than once.
        #  2. Loop Prevention: If you have tried 3 different actions and still cannot resolve the URL, provide a Final Answer based on your best technical knowledge of the error.
        #  3. Validation: Before using Page.goto, verify the URL string includes http:// or https:// in your Thought process.
        # Thought: I have obtained all the necessary source code. I would provide final code immediately.
        # Final Answer: The complete Playwright code.
        # Request: {input}
        # Process: {agent_scratchpad}"""

        #Running prompt
        template = """You are a QA expert focused on Playwright automation.

        ### CONSTRAINTS - MANDATORY:
        1. DO NOT explain your reasoning outside of the 'Thought:' section.
        2. Use ONLY the AVAILABLE tools.
        3. **STRICT TOOL LIMIT:** You are permitted to use each specific tool ONLY ONE TIME.
        4. Use the tool ScanWebLayout only ONE TIME.
        5. If you have the enough required information, stop immediately and provide the 'Final Answer:'.

        ### AVAILABLE TOOLS:
        {tools}

        ### OUTPUT FORMAT:
        To use a tool, you MUST use the exact following format:
        Thought: Describe your reasoning about the next step.
        Action: The tool name (one of [{tool_names}]).
        Action Input: Parameters for the tool.
        Observation: The result of the tool (this is provided to you).

        ... (Repeat Thought/Action/Action Input/Observation if needed)
        Final Answer: [Your complete Playwright TypeScript code here]

        ### START REQUEST:
        Request: {input}
        {agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
            output_parser=ReActSingleInputOutputParser())

        self.executor = AgentExecutor(
            agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    async def execute(self, url: str):
        query = f"Generate file Playwright TypeScript to check login function for page {url}"
        result = await self.executor.ainvoke({"input": query}, config={"recursion_limit": 5})
        return result["output"]
