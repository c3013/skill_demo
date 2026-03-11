"""skill_loader.py – discover and load LangChain tools from the skills package.

Each skill lives in its own sub-directory under ``skills/`` and **must** contain
a ``SKILL.md`` file with YAML front-matter that follows the Agent Skills
specification (https://agentskills.io/specification).  Any ``.py`` module in
the same directory is imported automatically; every :class:`BaseTool` instance
found inside those modules is collected and returned.

Directory layout
----------------
::

    skills/
    ├── calculator/
    │   ├── SKILL.md        # required – YAML front-matter + markdown instructions
    │   └── calculator.py   # optional – tool implementations
    ├── text/
    │   ├── SKILL.md
    │   └── text.py
    └── weather/
        ├── SKILL.md
        └── weather.py

SKILL.md format
---------------
::

    ---
    name: calculator
    description: Perform basic arithmetic operations …
    license: MIT
    ---

    # Calculator Skill

    ## When to Use
    …

Usage
-----
    from skill_loader import load_skills, SkillMetadata

    skills = load_skills()                   # load every skill
    skills = load_skills(["calculator"])     # load only the calculator skill

    for skill in skills:
        print(skill.metadata["name"], "–", skill.metadata["description"])
        for tool in skill.tools:
            print("  •", tool.name)
"""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

# Path to the skills package directory (sibling of this file)
_SKILLS_DIR = Path(__file__).parent / "skills"

# Agent Skills specification constraints
_MAX_SKILL_NAME_LENGTH = 64
_MAX_SKILL_DESCRIPTION_LENGTH = 1024

# SkillMetadata keys as defined by the Agent Skills specification
_REQUIRED_FRONTMATTER_KEYS = ("name", "description")


@dataclass
class SkillMetadata:
    """Parsed metadata from a skill's ``SKILL.md`` front-matter.

    Follows the `Agent Skills specification <https://agentskills.io/specification>`_.
    """

    name: str
    """Skill identifier (max 64 chars, lowercase alphanumeric and hyphens)."""

    description: str
    """What the skill does and when to use it (max 1 024 chars)."""

    path: str
    """Absolute path to the ``SKILL.md`` file."""

    license: Optional[str] = None
    """License name or reference to bundled license file."""

    compatibility: Optional[str] = None
    """Environment requirements (e.g. required packages, Python version)."""

    allowed_tools: list[str] = field(default_factory=list)
    """Tool names the skill recommends using."""

    metadata: dict[str, str] = field(default_factory=dict)
    """Arbitrary key-value mapping for additional metadata."""


@dataclass
class Skill:
    """A loaded skill: its parsed metadata and the LangChain tools it provides."""

    metadata: SkillMetadata
    """Parsed ``SKILL.md`` front-matter."""

    tools: list[BaseTool]
    """All :class:`~langchain_core.tools.BaseTool` instances from this skill."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_skill_name(name: str, directory_name: str) -> tuple[bool, str]:
    """Return ``(is_valid, error_message)`` for *name* per the Agent Skills spec."""
    if not name:
        return False, "name is required"
    if len(name) > _MAX_SKILL_NAME_LENGTH:
        return False, f"name exceeds {_MAX_SKILL_NAME_LENGTH} characters"
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return False, "name must not start/end with '-' or contain '--'"
    for ch in name:
        if ch == "-":
            continue
        if (ch.isalpha() and ch.islower()) or ch.isdigit():
            continue
        return False, f"invalid character '{ch}' in name"
    if name != directory_name:
        return False, f"name '{name}' must match directory name '{directory_name}'"
    return True, ""


def _parse_skill_md(skill_md_path: Path) -> Optional[SkillMetadata]:
    """Parse ``SKILL.md`` and return a :class:`SkillMetadata`, or ``None`` on error."""
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Cannot read %s: %s", skill_md_path, exc)
        return None

    # Extract YAML front-matter between leading '---' delimiters
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        logger.warning("Skipping %s: no valid YAML front-matter found", skill_md_path)
        return None

    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        logger.warning("Invalid YAML in %s: %s", skill_md_path, exc)
        return None

    if not isinstance(data, dict):
        logger.warning("Skipping %s: front-matter is not a mapping", skill_md_path)
        return None

    for key in _REQUIRED_FRONTMATTER_KEYS:
        if not str(data.get(key, "")).strip():
            logger.warning("Skipping %s: missing required field '%s'", skill_md_path, key)
            return None

    name = str(data["name"]).strip()
    description = str(data["description"]).strip()
    directory_name = skill_md_path.parent.name

    is_valid, error = _validate_skill_name(name, directory_name)
    if not is_valid:
        logger.warning(
            "Skill '%s' in %s does not follow the Agent Skills spec: %s",
            name,
            skill_md_path,
            error,
        )

    if len(description) > _MAX_SKILL_DESCRIPTION_LENGTH:
        logger.warning("Truncating long description in %s", skill_md_path)
        description = description[:_MAX_SKILL_DESCRIPTION_LENGTH]

    raw_tools = data.get("allowed-tools")
    if isinstance(raw_tools, list):
        allowed_tools = [str(t).strip(",") for t in raw_tools if str(t).strip(",")]
    elif isinstance(raw_tools, str):
        allowed_tools = [t.strip(",") for t in raw_tools.split() if t.strip(",")]
    else:
        allowed_tools = []

    raw_meta = data.get("metadata", {})
    metadata_map: dict[str, str] = (
        {str(k): str(v) for k, v in raw_meta.items()} if isinstance(raw_meta, dict) else {}
    )

    return SkillMetadata(
        name=name,
        description=description,
        path=str(skill_md_path),
        license=str(data.get("license", "")).strip() or None,
        compatibility=str(data.get("compatibility", "")).strip() or None,
        allowed_tools=allowed_tools,
        metadata=metadata_map,
    )


def _load_tools_from_dir(skill_dir: Path, package_prefix: str) -> list[BaseTool]:
    """Import every ``.py`` file in *skill_dir* and collect :class:`BaseTool` instances."""
    tools: list[BaseTool] = []
    for py_file in sorted(skill_dir.glob("*.py")):
        module_name = f"{package_prefix}.{py_file.stem}"
        spec = importlib.util.spec_from_file_location(module_name, py_file)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error importing %s: %s", py_file, exc, exc_info=True)
            continue
        for _attr, obj in inspect.getmembers(mod):
            if isinstance(obj, BaseTool) and obj not in tools:
                tools.append(obj)
    return tools


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_skills(names: Optional[list[str]] = None) -> list[Skill]:
    """Discover and load skills from the ``skills/`` directory.

    Each skill is expected to live in its own sub-directory containing a
    ``SKILL.md`` file.  Any ``.py`` module in that directory is imported
    automatically; every :class:`~langchain_core.tools.BaseTool` instance found
    inside those modules becomes part of the skill's tool list.

    Parameters
    ----------
    names:
        Optional list of skill *names* to load (matching the ``name`` field in
        ``SKILL.md`` / the directory name).  When ``None`` (default) every
        skill directory is loaded.

    Returns
    -------
    list[Skill]
        Ordered list of loaded :class:`Skill` objects.
    """
    skills: list[Skill] = []

    if not _SKILLS_DIR.is_dir():
        logger.warning("Skills directory not found: %s", _SKILLS_DIR)
        return skills

    for skill_dir in sorted(_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        # Apply optional name filter
        if names is not None and skill_dir.name not in names:
            continue

        meta = _parse_skill_md(skill_md)
        if meta is None:
            continue

        tools = _load_tools_from_dir(skill_dir, package_prefix=f"skills.{skill_dir.name}")
        skills.append(Skill(metadata=meta, tools=tools))

    return skills


def load_tools(names: Optional[list[str]] = None) -> list[BaseTool]:
    """Return a flat list of all :class:`~langchain_core.tools.BaseTool` instances.

    Convenience wrapper around :func:`load_skills` for callers that only need
    the tool objects without skill metadata.

    Parameters
    ----------
    names:
        Optional list of skill names to load (see :func:`load_skills`).
    """
    return [tool for skill in load_skills(names) for tool in skill.tools]
