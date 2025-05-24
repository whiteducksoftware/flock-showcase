import asyncio
import sys

import pydantic
from flock.core import Flock, FlockFactory, flock_type
from flock.tools import web_tools

# In case you experience issues with MCPs on Windows, you can try the following:
# Set up proper event loop policy for Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@flock_type
class InputModel(pydantic.BaseModel):
    url: str
    task: str


@flock_type
class FactuallyWrongComment(pydantic.BaseModel):
    comment: str
    author: str
    link: str
    answer: str
    date: str


playwright_mcp_server = FlockFactory.create_mcp_server(
    name="playwright-mcp-server",
    enable_tools_feature=True,
    connection_params=FlockFactory.StdioParams(
        command="npx", args=["-y", "@playwright/mcp@latest"]
    ),
)

flock = Flock(
    name="playwright_flock", servers=[playwright_mcp_server], model="openai/gpt-4.1"
)

playwright_agent = FlockFactory.create_default_agent(
    name="playwright_agent",
    input="input: InputModel",
    output="output: list[FactuallyWrongComment]",
    servers=[playwright_mcp_server],
    tools=[web_tools.web_search_tavily],
    enable_rich_tables=True,
    include_thought_process=True,
    use_cache=False,
    temperature=0.8,
    max_tokens=16000,
    max_tool_calls=100,
)
flock.add_agent(playwright_agent)


if __name__ == "__main__":
    try:
        input_model = InputModel(
            url="https://old.reddit.com/r/singularity/",
            task="Hello my dear agent! Visit threads and collect comments that are factually wrong. Do collect 5 comments. For each comment generate an answer disproving the comment with sources found with web_search_tavily",
        )

        result = flock.run(
            start_agent=playwright_agent,
            input={"input": input_model},
        )

        output = result.output
        print(output)
    finally:
        # Clean up any remaining tasks
        pending = asyncio.all_tasks()
        for task in pending:
            task.cancel()

        # Give tasks a chance to complete
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()
