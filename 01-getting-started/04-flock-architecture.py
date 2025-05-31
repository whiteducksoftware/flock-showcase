"""
Flock Unified Architecture Example

This example demonstrates Flock's new unified component architecture.
Instead of separate evaluators, modules, and routers, everything is now
a "component" - making the mental model much simpler.

Key concepts:
- Components: Unified building blocks for agents
- Three types: Evaluation, Routing, Utility
- Simple composition over complex inheritance
"""

from flock.components.evaluation.declarative_evaluation_component import (
    DeclarativeEvaluationComponent,
    DeclarativeEvaluationConfig,
)
from flock.components.routing.default_routing_component import (
    DefaultRoutingComponent,
    DefaultRoutingConfig,
)
from flock.components.utility.metrics_utility_component import (
    MetricsUtilityComponent,
    MetricsUtilityConfig,
)
from flock.components.utility.output_utility_component import (
    OutputUtilityComponent,
    OutputUtilityConfig,
)
from flock.core import Flock, FlockAgent

MODEL = "azure/gpt-4.1"

print("🏗️  Building Flock with Unified Architecture")
print("=" * 50)

# ================================
# 1. The New Mental Model
# ================================
print("\n1. OLD vs NEW Mental Model:")
print("   OLD: Agent + Evaluator + Router + Modules (4 concepts)")
print("   NEW: Agent + Components (2 concepts)")
print("   Components can be: Evaluation, Routing, or Utility")

# ================================
# 2. Building an Agent from Scratch
# ================================
print("\n2. Building an Agent Component by Component:")

# Start with an empty agent
research_agent = FlockAgent(
    name="research_agent",
    input="topic: str",
    output="summary: str, key_points: list[str], confidence_score: float",
)

print(f"   Created empty agent: {research_agent.name}")
print(f"   Components: {len(research_agent.components)}")

# Add evaluation component (replaces old "evaluator")
evaluation_component = DeclarativeEvaluationComponent(
    name="declarative_evaluator", config=DeclarativeEvaluationConfig()
)
research_agent.components.append(evaluation_component)
print(f"   Added evaluation component: {evaluation_component.name}")

# Add utility components (replaces old "modules")
output_component = OutputUtilityComponent(
    name="output_utility", config=OutputUtilityConfig()
)
research_agent.components.append(output_component)
print(f"   Added output utility: {output_component.name}")

metrics_component = MetricsUtilityComponent(
    name="metrics_utility", config=MetricsUtilityConfig()
)
research_agent.components.append(metrics_component)
print(f"   Added metrics utility: {metrics_component.name}")

print(f"   Final components: {len(research_agent.components)}")

# ================================
# 3. Chaining Agents with Routing
# ================================
print("\n3. Creating a Second Agent for Chaining:")

# Create a summary agent that will receive the research output
summary_agent = FlockAgent(
    name="summary_agent", input="research_data: dict", output="final_report: str"
)

# Add components to summary agent
summary_agent.components.extend(
    [
        DeclarativeEvaluationComponent(
            name="declarative_evaluator", config=DeclarativeEvaluationConfig()
        ),
        OutputUtilityComponent(name="output_utility", config=OutputUtilityConfig()),
    ]
)

print(
    f"   Created {summary_agent.name} with {len(summary_agent.components)} components"
)

# Now add routing to the research agent to chain to summary agent
routing_component = DefaultRoutingComponent(
    name="default_router", config=DefaultRoutingConfig(hand_off=summary_agent.name)
)
research_agent.components.append(routing_component)
print(f"   Added routing: {research_agent.name} -> {summary_agent.name}")

# ================================
# 4. Convenience Properties
# ================================
print("\n4. Backward Compatibility & Convenience:")
print(
    f"   research_agent.evaluator: {research_agent.evaluator.name if research_agent.evaluator else 'None'}"
)
print(
    f"   research_agent.router: {research_agent.router.name if research_agent.router else 'None'}"
)
utility_count = len(
    [c for c in research_agent.components if "utility" in c.name.lower()]
)
print(f"   research_agent utility components: {utility_count}")

# ================================
# 5. Running the Unified Architecture
# ================================
print("\n5. Running the Unified Flock:")

flock = Flock(name="unified_demo", model=MODEL)
flock.add_agent(research_agent)
flock.add_agent(summary_agent)

# Run with explicit workflow state tracking
print(f"   Starting with: {research_agent.name}")
result = flock.run(
    agent=research_agent,
    input={"topic": "The future of AI agent orchestration frameworks"},
)

# ================================
# 6. Component Inspection
# ================================
print("\n6. Architecture Inspection:")
for agent in flock.agents.values():
    print(f"\n   Agent: {agent.name}")
    print(f"   Components ({len(agent.components)}):")

    for i, component in enumerate(agent.components, 1):
        component_type = type(component).__name__
        if hasattr(component, "config"):
            config_type = type(component.config).__name__
        else:
            config_type = "No config"
        print(f"     {i}. {component.name} ({component_type})")
        print(f"        Config: {config_type}")

    print(f"   Next handoff: {getattr(agent, 'next_handoff', 'None')}")

print("\n🎉 Unified Architecture Demo Complete!")
print("\nKey Benefits:")
print("  ✓ Simpler mental model (2 concepts vs 4)")
print("  ✓ Explicit workflow state management")
print("  ✓ Backward compatibility maintained")
print("  ✓ Clean composition over inheritance")
print("  ✓ Easier testing and debugging")
