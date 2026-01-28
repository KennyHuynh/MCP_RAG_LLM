```text
PROJECT STRUCTURE:

project-root/
│
├── config/                 # SYSTEM CONFIGURATION
│   └── settings.py         # API keys, Model settings, Environment variables
│
├── prompts/                # LAYER 1: TEMPLATE LAYER (Prompt Management)
│   ├── __init__.py
│   ├── router_prompts.yaml # Prompts for classification logic
│   └── agent_prompts.yaml  # Prompts for specialized agents (Tech, Sales, etc.)
│
├── infrastructure/         # LAYER 2: RAG LAYER
│   ├── __init__.py
│   └── database.py         # Vector DB & Data indexing for RAG
│   
├── core/                   # LAYER 3 & 4: ROUTER & EXECUTION LAYER
│   ├── __init__.py
│   ├── llm_client.py       # Wrapper for OpenAI/Anthropic/Gemini/Ollama
│   ├── router.py           # Logic to classify/identify user's query
│   └── executor.py         # Logic to fetch prompts and execute reasoning
│
├── services/               # SERVICE LAYER (MCP & Utilities)
│   ├── __init__.py
│   └── logger.py           # Logging, Search, and DB service connectors
│
├── main.py                 # LAYER 5: INTERFACE LAYER (Entry point)
└── requirements.txt        # Project dependencies