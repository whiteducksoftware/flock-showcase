from flock.core import Flock, FlockFactory

github_mcp_server = FlockFactory.create_mcp_server(
    name="github-mcp-server",
    enable_tools_feature=True,
    connection_params=FlockFactory.StreamableHttpParams(
        url="https://server.smithery.ai/@smithery-ai/github/mcp?profile=<your-smithery-key>",
    ),
)

flock = Flock(name="github_flock", servers=[github_mcp_server])

github_agent = FlockFactory.create_default_agent(
    name="github_agent",
    input="project_idea: str",
    output="cool_project_name: str, created_repo_url: str, scaffold_file_list: list[str], "
    "implementation_plan: str, implementation_plan_created_issue_list: list[str], readme_content: str",
    servers=[github_mcp_server],
    enable_rich_tables=True,
    include_thought_process=True,
    max_tool_calls=100,
    max_tokens=32768,
    stream=True,
)
flock.add_agent(github_agent)

flock.run(
    start_agent=github_agent,
    input={"project_idea": "A puzzle game about cats as a web app!!"},
)
