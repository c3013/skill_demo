"""Calculator skill – basic arithmetic operations."""

import math

from langchain_core.tools import tool


@tool
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b


@tool
def divide(a: float, b: float) -> float:
    """Divide a by b. Raises ValueError if b is zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b


@tool
def square_root(x: float) -> float:
    """Return the square root of x. Raises ValueError for negative input."""
    if x < 0:
        raise ValueError("Cannot compute square root of a negative number.")
    return math.sqrt(x)
