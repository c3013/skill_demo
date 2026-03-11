"""main.py – LangChain skill invocation demo.

Demonstrates two modes:
1. **Direct invocation** – call individual tools directly without an LLM.
2. **Agent-based invocation** – an LLM-powered ReAct agent selects and calls
   the right tools automatically (requires OPENAI_API_KEY in the environment
   or a .env file).

Run
---
    # Direct invocation only (no API key needed):
    python main.py

    # Agent-based invocation (needs OPENAI_API_KEY):
    OPENAI_API_KEY=sk-... python main.py
    # or create a .env file with OPENAI_API_KEY=sk-... and run:
    python main.py
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.tools import BaseTool

from skill_loader import load_skills

load_dotenv()  # reads .env if present


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _separator(title: str) -> None:
    width = 60
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


# ---------------------------------------------------------------------------
# Part 1 – direct skill invocation
# ---------------------------------------------------------------------------

def demo_direct_invocation(tools: list[BaseTool]) -> None:
    """Show each tool's metadata and invoke a representative subset directly."""
    _separator("Part 1: Direct Skill Invocation (no LLM required)")

    print(f"\nLoaded {len(tools)} skill(s):\n")
    for tool in tools:
        print(f"  • {tool.name:<25} – {tool.description}")

    # --- Calculator demos ---
    _separator("Calculator skill examples")
    by_name: dict[str, BaseTool] = {t.name: t for t in tools}

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
# Part 2 – agent-based invocation (requires an LLM)
# ---------------------------------------------------------------------------

def demo_agent_invocation(tools: list[BaseTool]) -> None:
    """Use a LangGraph ReAct agent to answer questions using the loaded skills."""
    _separator("Part 2: Agent-Based Skill Invocation (requires OPENAI_API_KEY)")

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("sk-placeholder"):
        print(
            "\n  OPENAI_API_KEY not set – skipping agent demo.\n"
            "  Set OPENAI_API_KEY in your environment or in a .env file to enable it."
        )
        return

    try:
        from langchain_openai import ChatOpenAI
        from langgraph.prebuilt import create_react_agent
    except ImportError as exc:
        print(f"\n  Missing dependency: {exc}. Run: pip install langchain-openai langgraph")
        return

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_react_agent(llm, tools)

    questions = [
        "What is the square root of 256, and what is 13 multiplied by 7?",
        "How many words are in the sentence 'The quick brown fox jumps over the lazy dog'?",
        "What is the weather like in Tokyo and Shanghai right now?",
    ]

    for question in questions:
        print(f"\n  Question: {question}")
        response = agent.invoke({"messages": [("user", question)]})
        # The final answer is in the last AI message
        final = response["messages"][-1].content
        print(f"  Answer:   {final}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n🔧 LangChain Skill Demo – loading skills …")

    # Load all skills from the skills/ package
    tools = load_skills()

    # Part 1: direct invocation (always runs)
    demo_direct_invocation(tools)

    # Part 2: agent invocation (runs only when OPENAI_API_KEY is available)
    demo_agent_invocation(tools)

    _separator("Demo complete")
    print()


if __name__ == "__main__":
    main()
