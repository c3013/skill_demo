# LangChain Deep Agent Skill Demo

A Python demo that shows how to define and run **true skills** using the
[deepagents](https://docs.langchain.com/oss/python/deepagents/overview) library
together with the [Agent Skills specification](https://agentskills.io/specification).

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
├── skill_loader.py           # skill discovery, SKILL.md parsing, store loading
├── main.py                   # demo entry point
├── requirements.txt
└── .env.example
```

## How it works – the deepagents skill integration

```
┌─────────────────────────────────────────────┐
│            InMemoryStore                    │
│  namespace: ("filesystem",)                 │
│  ┌──────────────────────────────────────┐   │
│  │ /skills/calculator/SKILL.md          │   │
│  │ /skills/text/SKILL.md               │   │
│  │ /skills/weather/SKILL.md            │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
          ↕ StoreBackend reads/writes
┌─────────────────────────────────────────────┐
│      create_deep_agent(                     │
│          backend = StoreBackend,            │
│          store   = InMemoryStore,           │
│          skills  = ["/skills/"],            │
│          tools   = [add, subtract, …],      │
│      )                                      │
└─────────────────────────────────────────────┘
```

1. `load_skills_into_store(store)` reads every `SKILL.md` from disk and puts
   it into the `InMemoryStore` under namespace `("filesystem",)`.
2. `create_deep_agent` receives a `StoreBackend` factory and the `InMemoryStore`.
   Its `SkillsMiddleware` reads the `SKILL.md` files at startup and injects the
   skill instructions into the agent's system prompt.
3. The Python tool implementations (e.g. `add`, `get_weather`) are passed as
   `tools=` so the agent can call them to fulfill skill-guided requests.

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

### 2 – (Optional) Configure an LLM API key

Copy `.env.example` to `.env` and fill in your key to enable the deep-agent demo:

```bash
cp .env.example .env
# edit .env – set ANTHROPIC_API_KEY or OPENAI_API_KEY
```

The direct invocation demo works **without** any API key.

### 3 – Run the demo

```bash
python main.py
```

## Demo modes

### Part 1 – Direct skill invocation (no LLM)

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
  add(a=12, b=8) = 20.0
  multiply(a=6, b=7) = 42.0
  square_root(x=144) = 12.0
```

### Part 2 – Deep-agent skill invocation (requires `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`)

Skills are loaded into an `InMemoryStore`, a `deepagents` deep agent is created
with `StoreBackend`, and natural-language questions are answered using the skill
tools.

```python
from deepagents import create_deep_agent
from deepagents.backends import StoreBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from skill_loader import load_skills, load_skills_into_store, load_tools

store = InMemoryStore()
load_skills_into_store(store)          # populate SKILL.md files

agent = create_deep_agent(
    model="anthropic:claude-3-5-haiku-latest",
    tools=load_tools(),                # Python @tool implementations
    backend=(lambda rt: StoreBackend(rt)),
    store=store,
    skills=["/skills/"],              # where SKILL.md files live in the store
    checkpointer=MemorySaver(),
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is 13 × 7?"}]},
    config={"configurable": {"thread_id": "my-thread"}},
)
```

## Adding a new skill

1. Create a new directory `skills/my-skill/`.
2. Add `skills/my-skill/SKILL.md` with the required YAML front-matter.
3. Add `skills/my-skill/my_skill.py` with `@tool`-decorated functions.

The skill loader discovers all directories automatically — no other changes needed.

```
skills/my-skill/
├── SKILL.md       # name: my-skill, description: …
└── my_skill.py    # @tool functions
```

## Key dependencies

| Package | Version |
|---|---|
| `deepagents` | ≥ 0.4.0 |
| `langgraph` | ≥ 0.3.0 |
| `langchain` | ≥ 1.2 |
| `langchain-core` | ≥ 1.2 |
| `PyYAML` | ≥ 6.0 |
| `langchain-openai` | ≥ 1.1 (OpenAI model support) |
