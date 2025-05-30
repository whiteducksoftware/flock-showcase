from flock.core import Flock, FlockFactory

flock = Flock()

# --------------------------------
# Create an agent
# --------------------------------
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
flock.run(
    start_agent=presentation_agent,
    input={"topic": "A presentation about robot kittens!"},
)
