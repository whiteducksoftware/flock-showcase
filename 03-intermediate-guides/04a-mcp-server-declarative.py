
from flock.core import Flock, FlockFactory

github_mcp_server = FlockFactory.create_mcp_server(
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

flock = Flock(name="github_flock", servers=[github_mcp_server], model="openai/gpt-4.1")

github_agent = FlockFactory.create_default_agent(
    name="github_agent",
    input="project_idea: str",
    output="cool_project_name: str, repo_url: str, scaffold_file_list: list[str], "
    "implementation_plan: str, implementation_plan_issue_list: list[str], readme_content: str",
    servers=[github_mcp_server],
    enable_rich_tables=True,
    include_thought_process=True,
    use_cache=False,
    temperature=0.8,
    max_tokens=16000,
    max_tool_calls=100,
)
flock.add_agent(github_agent)

flock.run(
    agent=github_agent,
    input={"project_idea": "An app that generates better app ideas than my colleagues"},
)
