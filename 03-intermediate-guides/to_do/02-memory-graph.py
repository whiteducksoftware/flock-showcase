from flock.core import Flock, FlockFactory
from flock.modules.memory.memory_module import MemoryModuleConfig
from flock.tools import web_tools

MODEL = "openai/gpt-4o"

# docker run -p 7687:7687 memgraph/memgraph-mage:latest --schema-info-enabled=True
# Please start memgraph before running this script


# config = {
#     "embedder": {
#         "provider": "openai",
#         "config": {"model": "text-embedding-3-large", "embedding_dims": 1536},
#     },
#     "graph_store": {
#         "provider": "memgraph",
#         "config": {
#             "url": "bolt://localhost:7687",
#             "username": "memgraph",
#             "password": "xxx", # TODO: change to your memgraph password
#         },
#     },
#     "vector_store": {
#         "provider": "chroma",
#         "config": {
#             "collection_name": "flock_memory",
#             "path": ".flock/memory",
#         }
#     }
# }

flock = Flock(name="memory_graph_flock", model=MODEL, enable_logging=True)


simple_web_scraper = FlockFactory.create_default_agent(
    name="simple_web_scraper",
    description="A simple web scraper that collects the content of a given url",
    input="url",
    output="content",
    tools=[web_tools.web_content_as_markdown]
)
simple_web_scraper.add_component(config_instance=MemoryModuleConfig(enable_write_only_mode=True))
flock.add_agent(simple_web_scraper)


memory_agent = FlockFactory.create_default_agent(
    name="memory_agent",
    description="A simple agent that uses its memory to answer questions",
    input="query, memory",
    output="answer",
)
memory_agent.add_component(config_instance=MemoryModuleConfig(enable_read_only_mode=True))
flock.add_agent(memory_agent)

flock.run(
    start_agent=simple_web_scraper,
    input={"url": "https://lite.cnn.com/travel/alexander-the-great-macedon-persian-empire-darius/index.html"},
)


# flock.run(
#     start_agent=memory_agent,
#     input={"query": "What can you tell me about Alexander the Great?"},
# )


