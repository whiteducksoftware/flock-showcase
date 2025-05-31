from flock.core import Flock, FlockFactory

# --------------------------------
# Let's talk about models!
# --------------------------------
# Flock uses litellm to talk to LLMs
# Please consult the litellm documentation:
# https://docs.litellm.ai/docs/providers


# In this example we want to use a model via ollama to use a local model
# For this you need to install ollama:
# https://ollama.com/download
# And download a model - We will use a model of the qwen3 family which are SOTA in their respective parameter count:
# choose one which fits your hardware
# https://ollama.com/library/qwen3
# ollama run qwen3

# All you have to do is make sure the model id matches what litellm expects
# https://docs.litellm.ai/docs/providers/ollama
# Tip: the ollama_chat/model format seems to work better than ollama/model
MODEL = "ollama_chat/qwen3"

# Let's try a more difficult to set up provider
# We will use azure open ai
# https://docs.litellm.ai/docs/providers/azure

# The documentation tells you which env variables you need to set
# AZURE_API_KEY
# AZURE_API_BASE
# AZURE_API_VERSION

# Then set the model again with the correct id
# MODEL = "azure/<your_deploymet>"


flock = Flock(name="hello_flock", description="This is your first flock!", model=MODEL)


presentation_agent = FlockFactory.create_default_agent(
    name="my_presentation_agent",
    input="topic",
    output="fun_title, fun_slide_headers, fun_slide_summaries",
)
flock.add_agent(presentation_agent)


flock.run(
    agent=presentation_agent,
    input={"topic": "A presentation about robot kittens"},
)
