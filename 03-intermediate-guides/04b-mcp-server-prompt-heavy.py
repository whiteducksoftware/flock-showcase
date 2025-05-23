"""
Purpose: Demonstrating how to use Flock's MCP integration

Use Case: GitHub Repository Creator 🐙 - Create GitHub repositories from Flock.

Also highlights two different "philosophies" of how to build agents

Pure declarative agent (04a-mcp-server.py)
vs.
Prompt-heavy agent (04b-mcp-server.py)
"""

import os

from flock.core import Flock, FlockFactory

# --- Requirements ---
# Have Docker installed in its latest version
# Have a GitHub account
# Have a GitHub personal access token with repo permissions (https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
# Add the personal access token to the environment variable GITHUB_PERSONAL_ACCESS_TOKEN
#
# Checkout the Docker MCP catalog: https://hub.docker.com/catalogs/mcp

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


flock = Flock(name="github_flock", servers=[github_mcp_server], model="openai/gpt-4.1")

github_agent = FlockFactory.create_default_agent(
    name="github_agent",
    description="Based on the project idea provided by the user, this agent comes up with a concrete "
    "project name and scaffolds a basic project file structure for the project. "
    "Before doing this the Agent makes sure there is no existing repository with the same name. "
    "After this the agent will create an implementation plan and creates issues for the "
    "plan on GitHub. "
    "Finally the agent will fill the README with the project description, implementation plan and "
    "the issues created on GitHub.",
    input="project_idea: str | Project idea",
    output="repo_url: str | The url of the newly created GitHub repository, "
    "file_list: list[str] | A list of files that were created in the repository, ",
    servers=[github_mcp_server],
    include_thought_process=True,
    max_tool_calls=100,
)
flock.add_agent(github_agent)

flock.run(
    start_agent=github_agent,
    input={"project_idea": "A novel puzzle game as web app"},
)

# --- YOUR TURN! ---
# 1. Try to use the 04a-mcp-server.py to create a repository.
# 2. Try to use the 04b-mcp-server.py to create a repository.
#
# Which agent does produce the better results?
# How can you improve both agents while keeping their 'philosophy' (prompt-heavy vs pure declarative)?
