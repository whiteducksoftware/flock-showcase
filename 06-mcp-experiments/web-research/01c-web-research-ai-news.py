import datetime

from flock.core import Flock, FlockFactory, flock_type
from flock.tools import file_tools
from pydantic import BaseModel, Field

# Long-task planning and execution with Playwright MCP server


@flock_type
class ResearchRequest(BaseModel):
    task: str = Field(
        description="A detailed task description for the agent to follow."
    )
    urls: list[str] = Field(
        default_factory=list, description="A list of URLs for the agent to visit."
    )


@flock_type
class ResearchResult(BaseModel):
    title: str = Field(description="The title of a single research step.")
    summary: str = Field(description="A brief summary of the research step.")
    analysis: str = Field(
        description="An analysis of the importance or implications of the research step."
    )
    url: str = Field(description="The URL of the research step.")


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
    description="An agent that follows research requests."
    "Save the result as a beautifully designed html file 'ai_research_<todays_date>.html'.",
    input="req: ResearchRequest, date: str",
    output="news: list[ResearchResult], saved_to_file: str",
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

req = ResearchRequest(
    task="Visit the links in the url list and look for interesting AI-related news. "
    "When visiting these sites, really dig into MULTIPLE threads and articles and collect bits of informational context and insights. "
    "Beyond the sources provided also dig deep into three to five sources of your own choice for additional news. "
    "The goal is to collect a comprehensive and in-depth overview of the AI news of the last seven days, "
    "Content to collect: New models, research papers, libraries or frameworks, business news. "
    "Content to ignore: Personal stories, memes, tutorials, or other non-news content.",
    urls=[
        "https://old.reddit.com/r/singularity/",
        "https://old.reddit.com/r/LocalLLaMA/",
        "https://old.reddit.com/r/StableDiffusion/",
        "https://old.reddit.com/r/MachineLearning/",
        "https://old.reddit.com/r/mlscaling/",
        "https://ainativedev.io/",
        "https://github.com/trending?since=weekly",
        "https://the-decoder.com/",
        "https://paperswithcode.com/",
        "https://venturebeat.com/category/ai/",
        "https://www.deeplearning.ai/the-batch/",
        "https://techcrunch.com/tag/artificial-intelligence/",
        "https://www.theverge.com/ai-artificial-intelligence",
        "https://www.thealgorithmicbridge.com/",
        "https://jack-clark.net/",
        "https://cognitiverevolution.substack.com/",
    ],
)
todays_date = datetime.datetime.now().strftime("%Y-%m-%d")

result = flock.run(
    agent=playwright_agent,
    input={"req": req, "date": todays_date},
)
