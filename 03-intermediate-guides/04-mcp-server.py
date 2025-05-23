"""
Purpose: Demonstrating how to use Flock's MCP integration

Use Case: GitHub Repository Creator 🐙 - Create GitHub repositories from Flock.

"""

import os

from flock.core import Flock, FlockFactory

# --- Requirements ---
# Have Docker installed in its latest version
# Have a GitHub account
# Have a GitHub personal access token with repo permissions (https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
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
    description="This agent is responsible for creating a new GitHub repository and adding a README file to it.",
    input="project_idea: str | Project idea",
    output="repo_url: str | The url of the newly created GitHub repository",
    servers=[github_mcp_server],
)


flock.run(
    start_agent=github_agent, input={"project_idea": "A web app for tracking my plants"}
)
