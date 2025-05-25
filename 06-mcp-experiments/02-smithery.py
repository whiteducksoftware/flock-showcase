from flock.core import Flock, FlockFactory
from flock.core.logging.logging import configure_logging
from flock.tools import file_tools, web_tools

configure_logging(flock_level="DEBUG", external_level="DEBUG")


sequentialthinking = FlockFactory.create_mcp_server(
    name="sequentialthinking",
    enable_tools_feature=True,
    connection_params=FlockFactory.StdioParams(
        command="docker",
        args=[
            "run",
            "-i",
            "--init",
            "--rm",
            "mcp/sequentialthinking:latest",
        ],
    ),
)


flock = Flock(
    name="sequentialthinking",
    servers=[sequentialthinking, code_runner],
    model="openai/gpt-4.1",
)

thinking_agent = FlockFactory.create_default_agent(
    name="thinking_agent",
    description="An agent that can think and reason about a given query with the help of thinking tools, search the web for relevant information, and provide a short concise answer, which it will save to a file.",
    input="query: str",
    output="output: str | Short Concise Answer",
    servers=[sequentialthinking, code_runner],
    tools=[
        web_tools.web_search_tavily,
        file_tools.file_save_to_file,
    ],
    enable_rich_tables=True,
    include_thought_process=True,
    use_cache=False,
    temperature=0.8,
    max_tokens=16000,
    max_tool_calls=100,
)
flock.add_agent(thinking_agent)


result = flock.run(
    start_agent=thinking_agent,
    input={
        "query": "Bob was invited to participate in a game show, and he advanced to the final round. The final round offered Bob the chance to win a large sum by playing a game against the host. The host has 30 shiny prop coins, each of which is worth $1,000 if Bob manages to win them by playing the game. The host hides the coins in three different prize boxes and then shuffles their order. The only rule restricting the host's coin placement is that one box must contain at least 2 coins, and one box must contain 6 more coins than another box. In order to play, Bob must submit three guesses, one guess for the number of coins in each box. The box is then opened and the number of coins is revealed. If Bob's guess is a number greater than the number of coins in the box, Bob earns no coins. If Bob guesses a number equal to or less than the number of coins in the box, Bob wins a number of coins equal to his guess.If Bob plays uses the optimal strategy, what's the minimum amount of money he can win from the game?"
    },
)

output = result.output
print(output)
