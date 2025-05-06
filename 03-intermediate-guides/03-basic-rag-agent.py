from flock.core.flock import Flock
from flock.core.flock_factory import FlockFactory
from flock.core.tools.azure_tools import azure_search_query

# create a flock
flock = Flock(name="Rag Demo")
# create an agent
agent = FlockFactory.create_default_agent(
    name="Menu Assistant",
    description="An agent that queries Azure Search N-time (as defined by the number_of_searches parameter). Every try will change the query so more relevant results are found.",
    input="query, number_of_searches",
    output="answer",
    tools=[azure_search_query],
    include_thought_process=True,
)

# add the agent to the flock
flock.add_agent(agent)

flock.to_yaml_file("flock.yaml")

# run the agent
flock.run(
    agent,
    input={"query": "Wo ist die Turnhalle von Schattdecor?", "number_of_searches": 2},
)
