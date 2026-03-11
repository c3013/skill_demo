# LangChain Skill Demo

A Python demo that shows how to define, load, and execute **skills** using the
[Agent Skills specification](https://agentskills.io/specification) together with
the LangChain / LangGraph stack.

Each skill is a **self-contained directory** under `skills/` that contains:

- `SKILL.md` – required; YAML front-matter with the skill's metadata
  (name, description, license, …) followed by Markdown instructions for
  when and how to use the skill.
- One or more `.py` modules that implement the actual
  [LangChain tools](https://python.langchain.com/docs/concepts/tools/).

## Project structure

```
skill_demo/
├── skills/
│   ├── calculator/
│   │   ├── SKILL.md          # skill metadata + instructions
│   │   └── calculator.py     # tools: add, subtract, multiply, divide, square_root
│   ├── text/
│   │   ├── SKILL.md
│   │   └── text.py           # tools: to_uppercase, to_lowercase, count_words, …
│   └── weather/
│       ├── SKILL.md
│       └── weather.py        # tools: get_weather, list_supported_cities
├── skill_loader.py           # skill discovery, SKILL.md parsing, tool loading
├── main.py                   # demo entry point
├── requirements.txt
└── .env.example
```

## SKILL.md format

Every skill directory **must** contain a `SKILL.md` file whose content starts
with YAML front-matter enclosed in `---` delimiters:

```markdown
---
name: calculator
description: Perform basic arithmetic operations … Use when users ask to compute numeric expressions.
license: MIT
---

# Calculator Skill

## When to Use
- User asks to add, subtract, multiply, or divide numbers
…
```

Required fields: `name`, `description`.
Optional fields: `license`, `compatibility`, `allowed-tools`, `metadata`.

The `name` must match the parent directory name and follow the Agent Skills
naming rules (lowercase alphanumeric + hyphens, max 64 chars).

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

Skills are loaded, their `SKILL.md` metadata is displayed, and then tools are
invoked directly by name — no LLM in the loop.

```
Loaded 3 skill(s):

  📦 calculator  [License: MIT]
     Perform basic arithmetic operations …
     Tools: add, subtract, multiply, divide, square_root

  📦 text  [License: MIT]
     Manipulate and analyse text strings …
     Tools: to_uppercase, to_lowercase, count_words, reverse_text, extract_emails

  📦 weather  [License: MIT]
     Look up current weather conditions …
     Tools: get_weather, list_supported_cities

Calculator skill examples
  add(a=12, b=8) = 20
  multiply(a=6, b=7) = 42
  square_root(x=144) = 12.0

Text skill examples
  to_uppercase: HELLO, WORLD! …
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

## Adding a new skill

1. Create a new directory `skills/my-skill/`.
2. Add `skills/my-skill/SKILL.md` with the required YAML front-matter
   (see format above).
3. Add `skills/my-skill/my_skill.py` and decorate each function with
   `@tool` from `langchain_core.tools`.

```
skills/my-skill/
├── SKILL.md       # name: my-skill, description: …
└── my_skill.py    # @tool functions
```

The skill loader discovers all directories automatically on the next run —
no other changes needed.

```python
# skills/my-skill/my_skill.py
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
| `PyYAML` | ≥ 6.0 |
| `langchain-openai` | ≥ 1.1 (agent demo only) |
| `langgraph` | ≥ 1.1 (agent demo only) |

