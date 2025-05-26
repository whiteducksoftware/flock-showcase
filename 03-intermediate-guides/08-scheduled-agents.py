from flock.core import Flock, FlockFactory
from flock.tools import file_tools

# from flock.core.logging import configure_logging
# configure_logging(flock_level="DEBUG",external_level="DEBUG")

MODEL = "azure/gpt-4.1"

flock = Flock(name="scheduled_flock", description="This is a scheduled flock", model=MODEL)

my_joke_per_minute_agent = FlockFactory.create_scheduled_agent(
    name="my_joke_per_minute_agent",
    schedule_expression="every 2s",
    description="This agent generates a funny joke every minute." 
    "Loads all jokes from a joke.txt, generates a novel joke, and appends it to the file.",
    tools=[file_tools.file_read_from_file, file_tools.file_append_to_file],
    output="a_funny_new_joke, all_jokes: list[str]",
    temperature=1
)

flock.add_agent(my_joke_per_minute_agent)

# The scheduler hooks into the FastAPI lifespan cycle
flock.serve()

