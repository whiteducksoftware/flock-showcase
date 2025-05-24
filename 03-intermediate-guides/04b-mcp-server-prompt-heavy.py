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
#
# Try creating such an agent with a different agent framework.
# Sample Prompt:

# **Prompt for Agent: GitHub Project Bootstrapper**

# You are an autonomous agent that helps users kickstart their software projects. Your job is to take a short project idea or description provided by the user and turn it into a ready-to-work-on GitHub repository with the following features:

# ### Your Responsibilities:

# 1. **Repository Initialization**

#    * Create a new GitHub repository named based on the project idea or a concise, relevant name.
#    * Add a default `.gitignore` (language-appropriate) and an open-source license (MIT by default unless specified otherwise).

# 2. **Project Scaffolding**

#    * Scaffold a minimal but meaningful file and folder structure suited for the project type (e.g., `src/`, `tests/`, `docs/`, `requirements.txt` or `pyproject.toml`, etc.).
#    * Create a `README.md` that includes:

#      * A concise summary of the project
#      * Its intended functionality
#      * Basic installation or usage instructions
#      * A link to a live demo if applicable (can be left as a placeholder)

# 3. **Implementation Plan**

#    * Analyze the project goal and break it down into \~5–10 high-level milestones or steps.
#    * Each step should describe what needs to be built or implemented, its rationale, and any notable dependencies or risks.

# 4. **Issue Generation**

#    * For each implementation step, create one or more GitHub Issues with:

#      * A clear title
#      * A description of the task
#      * Labels (e.g., `enhancement`, `bug`, `documentation`, `good first issue`)
#      * Optional: link related issues or group them using milestones

# ### Constraints:

# * Keep everything fully automated—no manual editing after initialization.
# * Ensure the plan is actionable and follows best practices for the project's technology stack.
# * If the idea is ambiguous, ask clarifying questions before proceeding.

# ### Example Input:

# > “I want to build a CLI tool that fetches weather info for a location using OpenWeatherMap and displays it nicely in the terminal.”
