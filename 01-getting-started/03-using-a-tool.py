from flock.core import Flock, FlockFactory
from flock.core.logging.formatters.themes import OutputTheme

flock = Flock(model="openai/gpt-5")

read_website_fast_mcp_server = FlockFactory.create_mcp_server(
    name="read-website-fast-mcp-server",
    enable_tools_feature=True,
    connection_params=FlockFactory.StdioParams(
        command="npx",
        args=[
            "-y",
            "@just-every/mcp-read-website-fast"
        ],
    ),
)

flock.add_server(read_website_fast_mcp_server)

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
    "entities_and_metadata: list[dict[str, str]],"
    "type:Literal['news', 'blog', 'opinion piece', 'tweet']",
    servers=[read_website_fast_mcp_server],
    enable_rich_tables=True,  # Instead of the json output, you can use the rich library to render the output as a table
    output_theme=OutputTheme.aardvark_blue,  # flock also comes with a few themes
    use_cache=False,  # flock will cache the result of the agent and if the input is the same as before, the agent will return the cached result
)
flock.add_agent(agent)



# --------------------------------
# Run the agent
# --------------------------------
# ATTENTION: Big table incoming
# It's worth it tho!
result = flock.run(
    agent=agent,
    input={
        "url": "https://lite.cnn.com/travel/alexander-the-great-macedon-persian-empire-darius/index.html"
    },
)


