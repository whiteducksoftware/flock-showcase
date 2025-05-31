# 02-core-concepts/02-pydantic-types.py
"""
Purpose: Demonstrate using images in Flock
"""

import os

import dspy
from flock.cli.utils import print_warning
from flock.core import Flock, FlockFactory
from flock.core.flock_registry import (
    flock_type,  # Decorator for registering custom types
)
from pydantic import BaseModel, Field  # Import Pydantic components

MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4o")


@flock_type
class MyPetsInputModel(BaseModel):
    name: str = Field(..., description="The name of the pet.")
    image: dspy.Image = Field(..., description="A image of the pet.")


@flock_type
class MyPetsOutputModel(BaseModel):
    cuteness_factor: float = Field(..., description="A number between 0 and 100.")
    fur_color: str = Field(..., description="The color of the fur.")
    animal_type: str = Field(..., description="The type of animal.")
    cuteness_reasoning: str = Field(
        ..., description="A reasoning for the cuteness factor."
    )
    image_description: str = Field(..., description="A description of the image.")


# --------------------------------
# Create a new Flock instance
# --------------------------------
flock = Flock(name="image_example", model=MODEL)


pet_agent = FlockFactory.create_default_agent(
    name="pet_agent",
    input="pet_query: MyPetsInputModel",
    output="answer: MyPetsOutputModel",
)
flock.add_agent(pet_agent)


# --------------------------------
# Run the Flock
# --------------------------------

try:
    my_input = MyPetsInputModel(
        name="luna", image=dspy.Image.from_file(".assets/luna.jpg")
    )

    # also try lucy!

    # my_input = MyPetsInputModel(
    #     name="lucy", image=dspy.Image.from_file(".assets/lucy.jpg")
    # )
    result = flock.run(
        agent="pet_agent",
        input={"pet_query": my_input},
    )


except Exception as e:
    print_warning(f"Agent run failed: {e}")
    print_warning("Please ensure your API key is set and the model is accessible.")
