import random

from flock.core.flock import Flock
from flock.core.flock_factory import FlockFactory
from flock.core.flock_registry import flock_tool


@flock_tool
def get_specials():
    "Provides a list of specials from the menu."
    return """
        Special Soup: Clam Chowder
        Special Salad: Cobb Salad
        Special Drink: Chai Tea
        """


@flock_tool
def get_price(item: str):
    """Provides the price of the requested menu item.

    Args:
      item: The name of the menu item.
    """
    # random price between 5 and 15
    return f"${random.randint(5, 15)}"


#################################


# create a flock
flock = Flock(name="Own Tools Demo")

# create an agent
agent = FlockFactory.create_default_agent(
    name="Menu Assistant",
    description="You are a helpful assistant",
    input="query",
    output="answer",
    tools=[get_specials, get_price],
    # include_thought_process=True, # flock will include the thought process of the agent in the output if available
)

# add the agent to the flock
flock.add_agent(agent)

# run the agent
flock.run(agent, input={"query": "What is the price of the soup special?"})
# Try
# flock.run(agent, input={"query": "What is the sum of the prices of all specials?"})
