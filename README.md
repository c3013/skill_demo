# LangChain Skill Demo

A concise Python demo that shows how to **load** and **execute** skills (LangChain tools)
using the latest LangChain / LangGraph stack.

## Project structure

```
skill_demo/
├── skills/
│   ├── __init__.py
│   ├── calculator_skill.py   # arithmetic tools: add, subtract, multiply, divide, square_root
│   ├── text_skill.py         # text tools: uppercase, lowercase, word count, reverse, email extract
│   └── weather_skill.py      # mock weather tools: get_weather, list_supported_cities
├── skill_loader.py           # dynamic skill discovery & loading
├── main.py                   # demo entry point
├── requirements.txt
└── .env.example
```

## Quick start

### 1 – Install dependencies

```bash
pip install -r requirements.txt
```

### 2 – (Optional) Configure an OpenAI API key

Copy `.env.example` to `.env` and fill in your key to enable the agent demo:

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...
```

The direct invocation demo works **without** any API key.

### 3 – Run the demo

```bash
python main.py
```

## Demo modes

### Part 1 – Direct skill invocation

Skills (tools) are invoked directly by name, without an LLM in the loop.
This is useful for unit-testing individual skills or calling them from
application code.

```
Calculator skill examples
  add(a=12, b=8) = 20
  multiply(a=6, b=7) = 42
  square_root(x=144) = 12.0

Text skill examples
  to_uppercase: HELLO, WORLD! ...
  extract_emails: ['hello@example.com', 'support@demo.org']

Weather skill examples
  Weather in Beijing: Sunny, 22°C, humidity 40%.
```

### Part 2 – Agent-based skill invocation (requires `OPENAI_API_KEY`)

A LangGraph ReAct agent is given the full tool list and answers natural-language
questions by automatically choosing which tools to call.

```
Question: What is the square root of 256, and what is 13 multiplied by 7?
Answer:   The square root of 256 is 16 and 13 × 7 = 91.
```

## Adding new skills

1. Create a new file `skills/my_skill.py`.
2. Decorate each function with `@tool` from `langchain_core.tools`.
3. Restart the demo – `skill_loader.py` discovers all modules automatically.

```python
from langchain_core.tools import tool

@tool
def greet(name: str) -> str:
    """Return a personalised greeting."""
    return f"Hello, {name}!"
```

## Key dependencies

| Package | Version |
|---|---|
| `langchain` | ≥ 1.2 |
| `langchain-core` | ≥ 1.2 |
| `langchain-community` | ≥ 0.4 |
| `langchain-openai` | ≥ 1.1 (agent demo only) |
| `langgraph` | ≥ 1.1 (agent demo only) |
