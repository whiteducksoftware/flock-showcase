import os

from flock.core import Flock, FlockFactory, flock_type
from pydantic import BaseModel

github_mcp_server = FlockFactory.create_mcp_server(
    name="github-mcp-server",
    enable_tools_feature=True,
    connection_params=FlockFactory.StdioParams(
        command="docker",
        args=[
            "run",
            "-i",
            "--init",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN=" + os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN"),
            "mcp/github-mcp-server:latest",
        ],
    ),
)

# 1. Create the main orchestrator
my_flock = Flock(model="azure/gpt-4.1", servers=[github_mcp_server])


# pydantic class with titel, use_case_description, use_case_requirements
@flock_type
class UseCaseRequirements(BaseModel):
    titel: str
    use_case_description: str
    use_case_requirements: str


# 2. Declaratively define an agent
requirement_agent = FlockFactory.create_default_agent(
    name="requirement_agent",
    input="topic, repo_url",
    description="This agent generates github issues for a given topic and repo url",
    output="project_name, github_issues:list[UseCaseRequirements]",
    servers=[github_mcp_server],
    max_tool_calls=100,
    enable_rich_tables=True,
    include_thought_process=True,
    max_tokens=16000,
)

# 3. Add the agent to the Flock
my_flock.add_agent(requirement_agent)

# 4. Run the agent!
input_data = {
    "topic": "A lightweight, beautifully designed Outlook web client with integrated AI to assist in writing and summarizing emails.",
    "repo_url": "https://github.com/AndreRatzenberger/ai-agentic-devops",
}


result = my_flock.run(start_agent="requirement_agent", input=input_data)
