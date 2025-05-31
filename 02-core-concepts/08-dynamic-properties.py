from flock.core import Flock, FlockFactory
from flock.core.context.context import FlockContext

MODEL = "azure/gpt-4.1"

# -------------------------------------------------
# Create the flock
# -------------------------------------------------
flock = Flock(name="dynamic_demo", description="Dynamic-spec example", model=MODEL)


# -------------------------------------------------
# 1) Agent that builds a haiku from a topic
# -------------------------------------------------
def haiku_description(ctx: FlockContext) -> str:
    topic = ctx.get_variable("topic")
    return f"Haiku generator about “{topic}”"


haiku_agent = FlockFactory.create_default_agent(
    name="haiku_agent",
    input="topic",
    output="haiku",
)
# plug dynamic pieces into the *_spec attributes via the property setters
haiku_agent.description = haiku_description  # callable
haiku_agent.next_agent = "judge_agent"  # static str
flock.add_agent(haiku_agent)


# -------------------------------------------------
# 2) Agent that judges the haiku and decides what to do next
#    (next_agent is decided *at runtime*)
# -------------------------------------------------
def choose_next(ctx: FlockContext) -> str:
    # 'length' will be produced by this very agent
    length = ctx.get_variable("judge_agent.length")
    return "cheer_agent" if length == "long" else "apology_agent"


judge_agent = FlockFactory.create_default_agent(
    name="judge_agent",
    input="haiku",
    output="length : str | 'long' if >40chars or 'short'",
)
judge_agent.description = "Length judge"  # plain string also OK
judge_agent.next_agent = choose_next  # callable
flock.add_agent(judge_agent)

# -------------------------------------------------
# 3) Terminal agents
# -------------------------------------------------
apology_agent = FlockFactory.create_default_agent(
    name="apology_agent",
    input="haiku, length",
    output="message",
)
apology_agent.description = "Sorry, the haiku is too short."
flock.add_agent(apology_agent)

cheer_agent = FlockFactory.create_default_agent(
    name="cheer_agent",
    input="haiku, length",
    output="message",
)
cheer_agent.description = "Great haiku! Present it proudly!"
flock.add_agent(cheer_agent)

# -------------------------------------------------
# Run
# -------------------------------------------------
result = flock.run(
    agent=haiku_agent,
    input={"topic": "robot kittens exploring Mars"},
)

print(result.message)
