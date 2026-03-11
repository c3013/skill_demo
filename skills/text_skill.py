"""Text skill – common string manipulation operations."""

from langchain_core.tools import tool


@tool
def to_uppercase(text: str) -> str:
    """Convert a string to uppercase."""
    return text.upper()


@tool
def to_lowercase(text: str) -> str:
    """Convert a string to lowercase."""
    return text.lower()


@tool
def count_words(text: str) -> int:
    """Count the number of words in a string."""
    return len(text.split())


@tool
def reverse_text(text: str) -> str:
    """Reverse the characters in a string."""
    return text[::-1]


@tool
def extract_emails(text: str) -> list:
    """Extract all email addresses found in the provided text."""
    import re
    pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    return re.findall(pattern, text)
