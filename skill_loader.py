"""skill_loader.py – dynamically discover and load LangChain tools from the skills package.

Usage
-----
    from skill_loader import load_skills

    tools = load_skills()                   # load every skill
    tools = load_skills(["calculator"])     # load only the calculator skill module
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Optional

from langchain_core.tools import BaseTool

import skills as _skills_pkg


def load_skills(modules: Optional[list[str]] = None) -> list[BaseTool]:
    """Discover and return all LangChain tools defined in the *skills* package.

    Parameters
    ----------
    modules:
        Optional list of skill module *short names* (without the ``_skill`` suffix,
        e.g. ``["calculator", "text"]``).  When ``None`` (default) every module
        inside the ``skills`` package is loaded.

    Returns
    -------
    list[BaseTool]
        A flat list of every :class:`~langchain_core.tools.BaseTool` instance
        found across the requested modules.
    """
    tools: list[BaseTool] = []
    pkg_path = _skills_pkg.__path__
    pkg_name = _skills_pkg.__name__

    for _finder, module_name, _ispkg in pkgutil.iter_modules(pkg_path):
        # Apply optional filter
        if modules is not None:
            short_name = module_name.replace("_skill", "")
            if short_name not in modules and module_name not in modules:
                continue

        full_name = f"{pkg_name}.{module_name}"
        mod = importlib.import_module(full_name)

        for _attr_name, obj in inspect.getmembers(mod):
            if isinstance(obj, BaseTool):
                tools.append(obj)

    return tools
