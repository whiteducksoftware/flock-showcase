# 02-core-concepts/02-pydantic-types.py
"""
Purpose: Demonstrate using images in Flock
"""

import os

from flock.core import Flock, FlockFactory

MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4o")


# --------------------------------
# Create a new Flock instance
# --------------------------------
flock = Flock(name="image_example", model=MODEL)


# A whimsical agent that turns any sentence into Yoda-speak.
yoda_agent = FlockFactory.create_default_agent(
    name="yoda_translator",
    input="text",
    output="yoda_text",
)
flock.add_agent(yoda_agent)


# --------------------------------
# 2. Run Flock as a REST API
# --------------------------------


# This will start the Flock as a REST API
# It will also create a OpenAPI spec
# http://localhost:8344/docs
flock.start_api()

# With UI!
# flock.start_api(create_ui=True)
