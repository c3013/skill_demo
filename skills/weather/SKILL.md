---
name: weather
description: Look up current weather conditions (temperature, condition, humidity) for major cities. Use when users ask about the weather in a specific location or want to know which cities are supported.
license: MIT
---

# Weather Skill

## When to Use

- User asks for the current weather in a city
- User wants to know which cities have weather data available

## Available Tools

- `get_weather` – return weather conditions for a given city
- `list_supported_cities` – list all cities with real (mock) weather data

## Notes

This skill uses **mock data** — no external API key is required.
For unrecognised cities a randomised response is returned so the demo
remains self-contained.

Supported cities with deterministic data: Beijing, Shanghai, New York,
London, Tokyo.
