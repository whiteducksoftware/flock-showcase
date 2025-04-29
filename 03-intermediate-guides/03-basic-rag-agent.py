import random
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
  #include_thought_process=True, # flock will include the thought process of the agent in the output if available
)

# add the agent to the flock
flock.add_agent(agent)

# run the agent
flock.run(agent, input={"query": "Wann wurde Schattdecor gegründet?", "number_of_searches": 2})







