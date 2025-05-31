from flock.core import Flock, FlockFactory
from flock.tools import file_tools

# Long-task planning and execution with Playwright MCP server

playwright_mcp_server = FlockFactory.create_mcp_server(
    name="playwright-mcp-server",
    enable_tools_feature=True,
    connection_params=FlockFactory.StdioParams(
        command="npx", args=["-y", "@playwright/mcp@latest"]
    ),
)

flock = Flock(name="playwright_flock", servers=[playwright_mcp_server])

playwright_agent = FlockFactory.create_default_agent(
    name="playwright_agent",
    description="With playwright try to find following information in the web:"
    "What's the name of the last Album of musical artist of the user's input and when did it released?"
    "After this try to find three different reviews of the album and summarize them."
    "Based on these reviews, write a review on your own in a very well written style that is also the most funniest review ever written."
    "It should be written so well that it could be published on a music review website and should be free from 'GPT'-isms and other AI artifacts."
    "Save the review as a beautifully designed html file 'review_artist_albumname.html'.",
    input="musical_artist: str",
    output="review: str, saved_to_file: str",
    servers=[playwright_mcp_server],
    tools=[file_tools.file_save_to_file],
    enable_rich_tables=True,
    include_thought_process=True,
    use_cache=False,
    temperature=0.8,
    max_tokens=32000,
    max_tool_calls=100,
)
flock.add_agent(playwright_agent)


result = flock.run(
    agent=playwright_agent,
    input={"musical_artist": "God is an Astronaut"},
)
