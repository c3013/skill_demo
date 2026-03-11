"""main.py – LangChain Deep Agent skill demo.

Demonstrates two modes:
1. **Direct invocation** – call individual tools directly without an LLM.
2. **Deep-agent invocation** – a ``deepagents`` deep agent loads each skill's
   ``SKILL.md`` from a LangGraph ``InMemoryStore`` (via ``StoreBackend``) and
   uses the skill tools to answer questions.  Requires an LLM API key.

Each skill lives in its own sub-directory under ``skills/`` and is described
by a ``SKILL.md`` file that follows the Agent Skills specification
(https://agentskills.io/specification).

Run
---
    # Direct invocation only (no API key needed):
    python main.py

    # Deep-agent invocation (needs ANTHROPIC_API_KEY or OPENAI_API_KEY):
    ANTHROPIC_API_KEY=sk-ant-... python main.py
    # or create a .env file and run:
    python main.py
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.tools import BaseTool

from skill_loader import Skill, load_skills, load_skills_into_store, load_tools

load_dotenv()  # reads .env if present


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _separator(title: str) -> None:
    width = 60
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def _pick_model() -> str | None:
    """Return a model identifier based on available API keys, or None."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic:claude-3-5-haiku-latest"
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key.startswith("sk-") and not openai_key.startswith("sk-placeholder"):
        return "openai:gpt-4o-mini"
    return None


# ---------------------------------------------------------------------------
# Part 1 – direct skill invocation
# ---------------------------------------------------------------------------

def demo_direct_invocation(skills: list[Skill]) -> None:
    """Show each skill's SKILL.md metadata and invoke a representative subset directly."""
    _separator("Part 1: Direct Skill Invocation (no LLM required)")

    all_tools: list[BaseTool] = [tool for skill in skills for tool in skill.tools]

    print(f"\nLoaded {len(skills)} skill(s):\n")
    for skill in skills:
        meta = skill.metadata
        annotation_parts = []
        if meta.license:
            annotation_parts.append(f"License: {meta.license}")
        if meta.compatibility:
            annotation_parts.append(f"Compatibility: {meta.compatibility}")
        annotation = f"  [{', '.join(annotation_parts)}]" if annotation_parts else ""
        print(f"  📦 {meta.name}{annotation}")
        print(f"     {meta.description}")
        print(f"     Tools: {', '.join(t.name for t in skill.tools)}")
        print()

    # --- Calculator demos ---
    _separator("Calculator skill examples")
    by_name: dict[str, BaseTool] = {t.name: t for t in all_tools}

    cases = [
        ("add",         {"a": 12, "b": 8}),
        ("subtract",    {"a": 100, "b": 37}),
        ("multiply",    {"a": 6, "b": 7}),
        ("divide",      {"a": 22, "b": 7}),
        ("square_root", {"x": 144}),
    ]
    for name, kwargs in cases:
        if name in by_name:
            result = by_name[name].invoke(kwargs)
            args_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            print(f"  {name}({args_str}) = {result}")

    # --- Text skill demos ---
    _separator("Text skill examples")
    sample = "Hello, World! Contact us at hello@example.com or support@demo.org"
    text_cases = [
        ("to_uppercase",   {"text": sample}),
        ("to_lowercase",   {"text": sample}),
        ("count_words",    {"text": sample}),
        ("reverse_text",   {"text": "LangChain Skills"}),
        ("extract_emails", {"text": sample}),
    ]
    for name, kwargs in text_cases:
        if name in by_name:
            result = by_name[name].invoke(kwargs)
            print(f"  {name}: {result}")

    # --- Weather skill demos ---
    _separator("Weather skill examples")
    for city in ["Beijing", "London", "Atlantis"]:
        if "get_weather" in by_name:
            result = by_name["get_weather"].invoke({"city": city})
            print(f"  {result}")

    if "list_supported_cities" in by_name:
        cities = by_name["list_supported_cities"].invoke({})
        print(f"\n  Supported cities: {cities}")


# ---------------------------------------------------------------------------
# Part 2 – deep-agent invocation (requires an LLM API key)
# ---------------------------------------------------------------------------

def demo_deep_agent_invocation(skills: list[Skill]) -> None:
    """Create a deep agent backed by StoreBackend + InMemoryStore and run a demo query.

    Skills are loaded into the store so the agent's SkillsMiddleware can read
    their SKILL.md instructions at runtime.  The Python tool implementations
    are passed directly as the agent's tool list.
    """
    _separator("Part 2: Deep Agent Invocation (requires ANTHROPIC_API_KEY or OPENAI_API_KEY)")

    model = _pick_model()
    if model is None:
        print(
            "\n  No LLM API key found – skipping deep-agent demo.\n"
            "  Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your environment or .env file."
        )
        return

    try:
        from deepagents import create_deep_agent
        from deepagents.backends import StoreBackend
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.store.memory import InMemoryStore
    except ImportError as exc:
        print(f"\n  Missing dependency: {exc}. Run: pip install deepagents langgraph")
        return

    # ── 1. Create a LangGraph store and populate it with each skill's SKILL.md ──
    store = InMemoryStore()
    skill_keys = load_skills_into_store(store, skills_root="/skills/")
    print(f"\n  Loaded {len(skill_keys)} skill(s) into InMemoryStore:")
    for key in skill_keys:
        print(f"    • {key}")

    # ── 2. Collect all tool implementations from the skill Python modules ──
    all_tools: list[BaseTool] = [tool for skill in skills for tool in skill.tools]

    # ── 3. Create the deep agent ──
    #   • backend  – StoreBackend reads/writes files from the InMemoryStore
    #   • store    – the InMemoryStore populated with SKILL.md files above
    #   • skills   – virtual path prefix where skill directories live in the store
    #   • tools    – the actual @tool implementations from our skill .py modules
    #   • checkpointer – MemorySaver enables thread-based conversation history
    checkpointer = MemorySaver()
    agent = create_deep_agent(
        model=model,
        tools=all_tools,
        backend=(lambda rt: StoreBackend(rt)),
        store=store,
        skills=["/skills/"],
        checkpointer=checkpointer,
    )

    # ── 4. Ask the agent questions that exercise the skills ──
    questions = [
        "What is 13 multiplied by 7, and what is the square root of 256?",
        "How many words are in 'The quick brown fox jumps over the lazy dog'?",
        "What is the weather like in Tokyo and Shanghai?",
    ]

    thread_id = "skill-demo-thread"
    for question in questions:
        print(f"\n  Question: {question}")
        response = agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config={"configurable": {"thread_id": thread_id}},
        )
        final = response["messages"][-1].content
        # Trim very long responses for readability
        preview = final if len(final) <= 300 else final[:300] + " …"
        print(f"  Answer:   {preview}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n🔧 LangChain Deep Agent Skill Demo – loading skills …")

    # Load all skills from the skills/ directory (each skill has a SKILL.md)
    skills = load_skills()

    # Part 1: direct invocation (always runs, no LLM needed)
    demo_direct_invocation(skills)

    # Part 2: deep-agent invocation (requires an LLM API key)
    demo_deep_agent_invocation(skills)

    _separator("Demo complete")
    print()


if __name__ == "__main__":
    main()
