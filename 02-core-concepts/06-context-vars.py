from flock.core import Flock, FlockFactory

# --------------------------------
# Define the model
# --------------------------------
# Flock uses litellm to talk to LLMs
# Please consult the litellm documentation for valid IDs:
# https://docs.litellm.ai/docs/providers
MODEL = "azure/gpt-4.1"


# --------------------------------
# Create the flock and context
# --------------------------------
# The flock is the place where all the agents are at home
flock = Flock(name="hello_flock", description="This is your first flock!", model=MODEL)

# --------------------------------
# Create an agent
# --------------------------------
# The Flock doesn't believe in prompts (see the docs for more info)
# The Flock just declares what agents get in and what agents produce
# my_presentation_agent takes in a topic and outputs a
# funny_title, fun_slide_headers and fun_slide_summaries
presentation_agent = FlockFactory.create_default_agent(
    name="my_presentation_agent",
    input="topic",
    output="fun_slide_title, fun_slide_headers, fun_slide_summaries",
)
flock.add_agent(presentation_agent)


my_blog_agent = FlockFactory.create_default_agent(
    name="my_blog_agent",
    input="topic",
    output="fun_blog_title, fun_blog_content",
)
flock.add_agent(my_blog_agent)


crirtical_agent = FlockFactory.create_default_agent(
    name="my_critical_agent",
    input="fun_slide_title, fun_slide_headers, fun_slide_summaries, fun_blog_title, fun_blog_content",
    output="blog_or_slides : str | Should the blog or slides be used for the presentation, reason : str | Why did you choose the blog or slides",
)
flock.add_agent(crirtical_agent)

presentation_agent.next_agent = "my_blog_agent"
my_blog_agent.next_agent = "my_critical_agent"


# --------------------------------
# Run the flock
# --------------------------------
# Tell the flock who the starting agent is and what input to give it
flock.run(
    start_agent=presentation_agent,
    input={"topic": "A presentation about robot kittens!"},
)

# YOUR TURN!
# Try changing the output definition (line 29) by replacing "fun" with "boring"
# (boring_title, boring_slide_headers, boring_slide_summaries)
