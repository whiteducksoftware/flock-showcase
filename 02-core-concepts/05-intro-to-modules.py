"""
Implementing modules in Flock
"""

import asyncio
from typing import Any

from flock.core import Flock, FlockAgent, FlockContext
from flock.core.flock_module import FlockModule, FlockModuleConfig
from flock.core.flock_registry import flock_component
from flock.core.logging.logging import get_logger
from flock.evaluators.declarative.declarative_evaluator import (
    DeclarativeEvaluatorConfig,
)
from pydantic import Field

logger = get_logger("memory")

# To create a module implement FlockModule and FlockModuleConfig


class MyOwnMemoryModuleConfig(FlockModuleConfig):
    """
    This is a simple module that stores a single memory in a file.
    """

    memory_file: str = Field(
        default="memory.txt", description="The file to store the memory in."
    )


# Register the module with the @flock_component decorator
@flock_component(config_class=MyOwnMemoryModuleConfig)
class MyOwnMemoryModule(FlockModule):
    """
    This is a simple module that stores a single memory in a file.
    """

    name: str = "my_own_memory"
    config: MyOwnMemoryModuleConfig = MyOwnMemoryModuleConfig()

    ##########################################################
    # Initialization
    ##########################################################

    def __init__(self, name: str, config: MyOwnMemoryModuleConfig):
        super().__init__(name=name, config=config)

    ##########################
    # Business logic
    ##########################

    def save(self, memory: str):
        """
        Save the memory to the file.
        """
        with open(self.config.memory_file, "w") as f:
            f.write(memory)

    def load(self):
        """
        Load the memory from the file.
        """
        try:
            with open(self.config.memory_file, "r") as f:
                return f.read()
        except FileNotFoundError:
            return None

    ##########################################################
    # Flock integration
    # Flock provides following hooks to modules:
    # - on_initialize (called when the agent is created)
    # - on_pre_evaluate (called before the agent is evaluated)
    # - on_post_evaluate (called after the agent is evaluated)
    # - on_terminate (called when the agent is terminated)
    # - on_error (called when the agent is in an error state)
    ##########################################################

    # For our module we want to save the memory when the agent is terminated
    async def on_terminate(
        self,
        agent: Any,
        inputs: dict[str, Any],
        context: FlockContext | None = None,
        result: dict[str, Any] | None = None,
    ):
        """
        This is called when the agent is terminated.
        """
        inputs = inputs.get("query", "")
        answer = result.get("answer", "")
        self.save(inputs + " " + answer)
        logger.info("Saved memory: " + inputs + " " + answer)

    # For our module we want to load the memory when the agent is initialized
    # We load the memory and pass it in the agent's description
    async def on_initialize(
        self,
        agent: FlockAgent,
        inputs: dict[str, Any],
        context: FlockContext | None = None,
    ):
        """
        This is called when the flock agent starts.
        """
        memory = self.load()
        agent.description = f"{agent.description}\n\nThis is your memory: {memory}"
        if memory:
            logger.info("Loaded memory: " + memory)
        else:
            logger.info("No memory found")


async def main():
    flock = Flock(enable_logging=True)

    # Create a new agent - this time without the factory
    agent = FlockAgent(
        name="my_memory_agent",
        description="You are a helpful assistant.",
        input="query",
        output="answer",
    )

    # This agent is now missing an evaluator
    eval_config = DeclarativeEvaluatorConfig()
    agent.add_component(
        config_instance=eval_config,
        component_name="default",
    )

    # Add the module to the agent
    agent.add_component(
        config_instance=MyOwnMemoryModuleConfig(), component_name="my_memory_module"
    )

    flock.add_agent(agent)

    # Run the flock (set breakpoints in the module hooks!)
    await flock.run_async(input={"query": "What is the capital of France?"})


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
