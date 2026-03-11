---
name: calculator
description: Perform basic arithmetic operations including addition, subtraction, multiplication, division, and square root. Use when users ask to compute numeric expressions.
license: MIT
---

# Calculator Skill

## When to Use

- User asks to add, subtract, multiply, or divide two numbers
- User asks for the square root of a number
- User needs to evaluate a numeric arithmetic expression

## Available Tools

- `add` – add two numbers together
- `subtract` – subtract *b* from *a*
- `multiply` – multiply two numbers together
- `divide` – divide *a* by *b* (raises `ValueError` when *b* is zero)
- `square_root` – return the square root of a non-negative number

## Notes

All operations accept and return `float` values.
Division by zero and square root of negative numbers raise a `ValueError`.
