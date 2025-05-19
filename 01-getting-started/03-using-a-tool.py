from flock.core import Flock, FlockFactory
from flock.core.logging.formatters.themes import OutputTheme
from flock.tools import code_tools, web_tools

# Define the DEFAULT_MODEL in your .env file
flock = Flock(model="openai/gpt-4o")

# --------------------------------
# Create an agent
# --------------------------------
# Some additions to example 01
# - you can define the output types of the agent with standard python type hints
# - you can define the tools the agent can use
# - you can define if the agent should use the cache
#   results will get cached and if true and if the input is the same as before, the agent will return the cached result
#   this is useful for expensive operations like web scraping and for debugging
# Some people need some swag in their output
# Flock supports rendering the output as a table and you can choose a theme (out of like 300 or so)
agent = FlockFactory.create_default_agent(
    name="my_agent",
    input="url",
    output="title, headings: list[str],"
    "entities_and_metadata: list[dict[]],"
    "type:Literal['news', 'blog', 'opinion piece', 'tweet']",
    tools=[web_tools.web_content_as_markdown],
    enable_rich_tables=True,  # Instead of the json output, you can use the rich library to render the output as a table
    output_theme=OutputTheme.aardvark_blue,  # flock also comes with a few themes
    use_cache=True,  # flock will cache the result of the agent and if the input is the same as before, the agent will return the cached result
    wait_for_input=True,  # flock will wait for the user to press enter before continuing after this agent's run
)
flock.add_agent(agent)


# --------------------------------
# Tools = ReAct Agent
# --------------------------------
# If tools are used, the agent will be a ReAct Agent
# ReAct Agents are agents that can use tools to solve tasks
# by planning steps, executing them and evaluating the results.
# With 'include_thought_process=True', the agent will include the thought process in the output
# This is useful for debugging and for understanding the agent's thought process
age_agent = FlockFactory.create_default_agent(
    name="my_celebrity_age_agent",
    input="a_person",
    output="persons_age_in_days",
    tools=[web_tools.web_search_duckduckgo, code_tools.code_code_eval],
    enable_rich_tables=True,
    output_theme=OutputTheme.homebrew,
    use_cache=True,  # flock will cache the result of the agent and if the input is the same as before, the agent will return the cached result
    include_thought_process=True,  # flock will include the thought process of the agent in the output if available
)
flock.add_agent(age_agent)


# --------------------------------
# Run the agent
# --------------------------------
# ATTENTION: Big table incoming
# It's worth it tho!
result = flock.run(
    start_agent=agent,
    input={
        "url": "https://lite.cnn.com/travel/alexander-the-great-macedon-persian-empire-darius/index.html"
    },
)

# To start a different agent, you can do so by calling flock.run() again with a different start_agent

result = flock.run(
    start_agent=age_agent,
    input={"a_person": "Brad Pitt"},
)

# --------------------------------
# YOUR TURN
# --------------------------------
# - Create a small research agent that can search the web for a given topic, convert the output to markdown and then use the markdown to create a beautiful report
# - Explore some of the other tools flock has to offer
