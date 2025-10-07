import asyncio

from pydantic import BaseModel

from flock.mcp import StdioServerParameters
from flock.orchestrator import Flock
from flock.registry import flock_tool, flock_type

# Register tools with flock_tool decorator
@flock_tool
def write_file(string: str, file_path: str) -> None:
    with open(file_path, "w") as f:
        f.write(string)


@flock_type
class Task(BaseModel):
    description: str


@flock_type
class Report(BaseModel):
    file_path: str
    title: str
    researched_urls: list[str]
    headings: list[str]
    summary: str


flock = Flock(model="openai/gpt-4.1")


# Here we add the read-website-fast MCP server which allows agents to read website content quickly
# using the `@just-every/mcp-read-website-fast` package.
flock.add_mcp(
    name="read-website-fast-mcp-server",
    enable_tools_feature=True,
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@just-every/mcp-read-website-fast"],
    ),
)


(
    flock.agent("web_researcher")
    .description("Researches info on the web and writes a report to report.md")
    .consumes(Task)
    .with_mcps(["read-website-fast-mcp-server"])
    .with_tools([write_file])
    .publishes(Report)
)


# 4. Run!
async def main():
    task = Task(
        description="Find the latest news articles about AI advancements and summarize it." 
        "Search at least 3 different websites and include the headings of each article."
    )
    await flock.publish(task)
    await flock.run_until_idle()
    print("✅ Website research report generated!")


asyncio.run(main())
