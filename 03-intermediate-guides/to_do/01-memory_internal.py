from flock.core import Flock, FlockFactory
from flock.modules.memory.memory_module import MemoryModuleConfig
from flock.tools import web_tools

MODEL = "openai/gpt-4o"


flock = Flock(name="memory_flock", model=MODEL)


chatty_agent = FlockFactory.create_default_agent(
    name="my_chatty_agent",
    description="A chatty agent with a memory",
    input="query, memory",
    output="answer",
    tools=[web_tools.web_content_as_markdown],
)
chatty_agent.add_component(config_instance=MemoryModuleConfig())
flock.add_agent(chatty_agent)

# flock.run(
#     agent=chatty_agent,
#     input={"query": "Please remember the main news of today as seen on https://lite.cnn.com/"},
# )


flock.run(
    agent=chatty_agent,
    input={"query": "What Trump news do you remember without using the web?"},
)
