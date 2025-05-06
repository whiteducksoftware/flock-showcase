from flock.core import Flock, FlockAgent
from flock.evaluators.declarative.declarative_evaluator import (
    DeclarativeEvaluatorConfig,
)
from flock.modules.output.output_module import OutputModuleConfig
from flock.modules.performance.metrics_module import (
    MetricsModuleConfig,
)

MODEL = "openai/gpt-4o"
flock = Flock(name="flock_architecture", model=MODEL)

# --------------------------------
# The anatomy of a flock agent
# --------------------------------
# So far we created agents with the create_default_agent function
# This function creates an agent with a default configuration and component set up
# The default agent includes the following modules:
#         - DeclarativeEvaluator
#         - OutputModule
#         - MetricsModule
#
# Let's create an agent from scratch and look into how an agent is built
# This is the most basic agent that you can create and it'll do nothing
# An agent on its own is basically a container for the following components:
# - input/output contract, which defines what kind of data the agent can handle and what it (should) produce
# - tools, which are the tools (eg. functions) that the agent can use
# - evaluator, which defines how an agent evaluates itself to produce an output
# - modules, which can trigger during the agent's lifecycle (like on_initialize, on_post_evaluate, etc.)
#   think modules = functionality YOU as the dev want to control
#         tools = functionality THE AGENT controls
# - handoff_router, which defines what the agent should do with the output (usually give it to the next agent)

empty_agent = FlockAgent(
    name="my_naked_agent",
    input="query",
    output="answer",
    tools=None,
    evaluator=None,
    modules=None,
    handoff_router=None,
)

# Flock's core library comes with a few modules and evaluators
# You can find more about them in the docs:
# ...

# To live the declarative philosophy you just need to pass the config instance to the .add_component method
# You tell Flock what you want. Flock handles the rest
# An agent can have multiple modules but it can only have one evaluator and one handoff_router
empty_agent.add_component(
    config_instance=DeclarativeEvaluatorConfig(), component_name="declarative_evaluator"
)
empty_agent.add_component(
    config_instance=OutputModuleConfig(), component_name="output_module"
)
empty_agent.add_component(
    config_instance=MetricsModuleConfig(), component_name="metrics_module"
)

flock.add_agent(empty_agent)


flock.run(
    start_agent=empty_agent,
    input={"query": "Hello"},
)
