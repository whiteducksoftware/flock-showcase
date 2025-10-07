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
    high_impact_info: dict[str, str]


flock = Flock(model="openai/gpt-4.1")


flock.add_mcp(
    name="browse_web",
    enable_tools_feature=True,
    connection_params=StdioServerParameters(
        command="npx",
        args=[
        "-y",
        "@playwright/mcp@latest",
      ]
    ),
)

(
    flock.agent("web_researcher")
    .description("Researches info on the web and writes a report to report.md")
    .consumes(Task)
    .with_mcps(["browse_web"])
    .with_tools([write_file])
    .publishes(Report)
)


# 4. Run!
async def main():
    task = Task(
        description="What are the current top trends in AI for 2025?" 
    )
    await flock.publish(task)
    await flock.run_until_idle()
    print("✅ Website research report generated!")


asyncio.run(main())
