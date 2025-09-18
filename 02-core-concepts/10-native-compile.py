"""
02-core-concepts/10-native-compile.py

Native LLMCompiler-style Program demo: plan parallelizable tool calls, then synthesize a receipt.

Usage
- Set a model (e.g., export DEFAULT_MODEL="openai/gpt-4o" and OPENAI_API_KEY)
- Set FLOCK_USE_NATIVE_EVALUATOR=1 or set program_type explicitly as below.

The example simulates parallel fetches (prices, shipping, tax) and synthesizes a final receipt.
"""

from __future__ import annotations

import os
from typing import Any

from flock.core import Flock
from flock.core import DefaultAgent


# --- Demo store tools (in-memory) ---
CATALOG: dict[str, float] = {
    "widget": 12.50,
    "gizmo": 7.99,
    "doohickey": 4.25,
}


def fetch_product_price(name: str) -> float:
    """Return mock price for an item from the catalog."""
    return float(CATALOG.get(name.lower(), 0.0))


def fetch_shipping_rate(country: str) -> float:
    """Return a mock flat shipping rate by country."""
    table = {"de": 4.0, "us": 6.0, "fr": 5.0, "uk": 5.5}
    return float(table.get(country.lower(), 8.0))


def fetch_tax_rate(country: str) -> float:
    """Return a mock tax rate (0.0–0.25)."""
    table = {"de": 0.19, "us": 0.07, "fr": 0.20, "uk": 0.20}
    return float(table.get(country.lower(), 0.10))


def main() -> None:
    model = os.getenv("DEFAULT_MODEL", "")
    flock = Flock(name="native-compile-demo", model=model, show_flock_banner=False)

    agent = DefaultAgent(
        name="compiler",
        description=(
            "Given a shopping request, plan parallel tool calls to fetch item prices,"
            " the shipping rate, and the tax rate, then synthesize a final receipt."
        ),
        input=(
            "country: str | destination country; items: list[str] | list of item names"
        ),
        output=(
            "total: number | final total including shipping and tax;"
            "breakdown: list[dict[str,string]] | line items and amounts;"
            "note: str | a short human-readable summary"
        ),
        tools=[fetch_product_price, fetch_shipping_rate, fetch_tax_rate],
        temperature=0.2,
        max_tool_calls=8,
    )
    flock.add_agent(agent)

    # Force native LLMCompiler program if env is not set
    agent.evaluator.config.use_native = agent.evaluator.config.use_native or True
    agent.evaluator.config.program_type = "llm_compiler"

    request = {"country": "DE", "items": ["widget", "gizmo"]}
    result = flock.run(agent=agent, input=request, box_result=False)
    print("\nNative LLMCompiler result:\n", result)


if __name__ == "__main__":
    main()

