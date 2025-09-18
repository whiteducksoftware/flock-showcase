"""02-core-concepts/09-native-react.py

Native ReAct Program demo with simple Python tools (no external deps).

Usage
- Set a model (e.g., export DEFAULT_MODEL="openai/gpt-4o" and OPENAI_API_KEY)
- Option A: set env FLOCK_USE_NATIVE_EVALUATOR=1
- Option B (explicit): set agent.evaluator.config.use_native = True and program_type = "react"

This example keeps tools local and safe to run. The model decides when to call them.
"""

from __future__ import annotations

import os

from flock.core import DefaultAgent, Flock


# --- Simple local tools ---
def compute(expression: str) -> str:
    """Evaluate a simple arithmetic expression safely (digits + ops)."""
    print(f"Computing {expression}")
    expr = expression.replace(" ", "")
    if not expr or any(ch not in "0123456789+-*/()." for ch in expr):
        return "unsupported expression"
    try:
        # Evaluate with restricted globals
        value = eval(expr, {"__builtins__": {}}, {})
        return str(value)
    except Exception as e:
        return f"error: {e}"


def get_weather(city: str) -> str:
    """Return a mock weather for a given city (demo stub)."""
    print(f"Getting weather for {city}")
    table = {
        "paris": "Cloudy, 21°C",
        "london": "Light rain, 18°C",
        "munich": "Sunny, 23°C",
        "san francisco": "Foggy, 17°C",
    }
    return table.get(city.lower(), "Weather data not available")


def lookup_exchange_rate(base: str, target: str) -> float:
    """Return a mock FX rate (demo stub)."""
    print(f"Looking up exchange rate for {base} to {target}")
    rates = {
        ("usd", "eur"): 0.91,
        ("eur", "usd"): 1.10,
        ("usd", "gbp"): 0.79,
        ("gbp", "usd"): 1.27,
    }
    return rates.get((base.lower(), target.lower()), 1.0)


def main() -> None:
    model = os.getenv("DEFAULT_MODEL", "")

    flock = Flock(name="native-react-demo", model=model, show_flock_banner=False)
    agent = DefaultAgent(
        name="reactor",
        description=(
            "You are a helpful assistant. Use the tools to compute answers when needed,"
            " then provide a concise final answer."
        ),
        input=("question: str | A user question possibly requiring tools"),
        output=("answer: str | The final concise answer"),
        tools=[compute, get_weather, lookup_exchange_rate],
        temperature=0.2,
        max_tool_calls=6,
    )
    flock.add_agent(agent)

    # Explicitly opt-in to native ReAct if env flag is not set
    agent.evaluator.config.use_native = agent.evaluator.config.use_native or True
    agent.evaluator.config.program_type = "react"

    # Query that encourages tool usage
    q = (
        "What is 23*7 and what's the weather in Paris? Also, what's the usd→eur rate?"
    )
    result = flock.run(agent=agent, input={"question": q}, box_result=False)
    print("\nNative ReAct result:\n", result)


if __name__ == "__main__":
    main()

