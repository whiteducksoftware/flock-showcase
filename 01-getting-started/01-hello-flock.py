from flock.core import Flock, FlockFactory

# 1. Create the main orchestrator
my_flock = Flock(model="openai/gpt-4.1")

# 2. Declaratively define an agent
brainstorm_agent = FlockFactory.create_default_agent(
    name="idea_generator", input="topic", output="catchy_title, key_points"
)

# 3. Add the agent to the Flock
my_flock.add_agent(brainstorm_agent)

# 4. Run the agent!
input_data = {"topic": "The future of AI agents"}
result = my_flock.run(agent="idea_generator", input=input_data)

# The result is a dot-accessible object ready for downstream tasks
print(f"Generated Title: {result.catchy_title}")
print(f"Key Points: {result.key_points}")
