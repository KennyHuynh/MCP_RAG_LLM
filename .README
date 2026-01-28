project-root/
│
├── config/                 # System configuration (API keys, Model settings)
│   └── settings.py
│
├── prompts/                # LAYER 1: TEMPLATE LAYER (Manage all Prompts)
│   ├── __init__.py
│   ├── router_prompts.yaml # Prompt for classify
│   └── agent_prompts.yaml  # Prompt for agent (Tech, Sales...)
│
├── infrastructure/         # LAYER 2: RAG LAYER
│   ├── __init__.py
│   └── database.py         # Store data to RAG
│   
|
├── core/                   # LAYER 3 & 4: ROUTER & EXECUTION LAYER
│   ├── __init__.py
│   ├── llm_client.py       # Wrapper for connecting to OpenAI/Anthropic/Gemini/Ollama
│   ├── router.py           # Logic to identify user's query
│   └── executor.py         # Logic to pick up prompt và execute answer
│
├── services/               # Additional Layer- Service Layer- for MCP (For example: DB, Log, Search)
│   └── logger.py
│
├── main.py                 # LAYER 5: INTERFACE LAYER (Entry point)
└── requirements.txt