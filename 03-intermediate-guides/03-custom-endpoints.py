# 02-core-concepts/02-pydantic-types.py
"""Purpose: Demonstrate using images in Flock"""

import os

import dspy
from flock.core import Flock, FlockFactory
from flock.core.api.custom_endpoint import FlockEndpoint
from flock.core.flock_registry import (
    flock_type,  # Decorator for registering custom types
)
from pydantic import BaseModel, Field  # Import Pydantic components

MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4o")

# --------------------------------
# Create a new Flock instance
# --------------------------------
flock = Flock(name="endpoint_example", model=MODEL)


# --------------------------------
# Pet agent
# --------------------------------


@flock_type
class MyPetsInputModel(BaseModel):
    image: dspy.Image = Field(..., description="A image of the pet.")


@flock_type
class MyPetsOutputModel(BaseModel):
    name: str = Field(..., description="A cute name fitting for the pet.")
    cuteness_factor: float = Field(..., description="A number between 0 and 100.")
    fur_color: str = Field(..., description="The color of the fur.")
    animal_type: str = Field(..., description="The type of animal.")
    cuteness_reasoning: str = Field(
        ..., description="A reasoning for the cuteness factor."
    )
    image_description: str = Field(..., description="A description of the image.")


pet_agent = FlockFactory.create_default_agent(
    name="pet_agent",
    input="pet_query: MyPetsInputModel",
    output="answer: MyPetsOutputModel",
)
flock.add_agent(pet_agent)


# --------------------------------
# Yoda agent
# --------------------------------


class YodaRequest(BaseModel):
    text: str


class YodaResponse(BaseModel):
    yoda_text: str


yoda_agent = FlockFactory.create_default_agent(
    name="yoda_translator",
    input="text",
    output="yoda_text",
)
flock.add_agent(yoda_agent)


# --------------------------------
# Endpoints
# --------------------------------


# Endpoint with body
async def yoda_endpoint(body: YodaRequest, flock: Flock | None = None) -> YodaResponse:  # type: ignore[valid-type]
    """Translate :pyattr:`YodaRequest.text` into the wisdom of Master Yoda."""
    result = await flock.run_async(start_agent=yoda_agent, input={"text": body.text})
    return YodaResponse(yoda_text=result["yoda_text"])


yoda_route = FlockEndpoint(
    path="/api/yoda",
    methods=["POST"],
    callback=yoda_endpoint,
    request_model=YodaRequest,
    response_model=YodaResponse,
    summary="Translate English into Yoda-speak",
    description="Fun demo endpoint powered by a single Flock agent.",
)


# Endpoint with query parameters


class ImageUrlParams(BaseModel):
    img_url: str


async def image_endpoint(query: ImageUrlParams, flock: Flock) -> MyPetsOutputModel:
    my_input = MyPetsInputModel(image=dspy.Image.from_url(query.img_url))
    result = await flock.run_async(
        start_agent="pet_agent",
        input={"pet_query": my_input},
    )
    return result.answer


img_url_route = FlockEndpoint(
    path="/api/cute-pet",
    methods=["GET"],
    callback=image_endpoint,
    query_model=ImageUrlParams,
    response_model=MyPetsOutputModel,
    summary="Calculates the cuteness of a pet",
    description="Takes an image url and returns a description of the pet.",
)


# Endpoint with query parameters without agent


class WordCountResponse(BaseModel):
    count: int


class WordCountParams(BaseModel):
    text: str


async def word_count(query: WordCountParams):
    return WordCountResponse(count=len(query.text.split()))


word_count_route = FlockEndpoint(
    path="/api/word_count",
    methods=["GET"],
    callback=word_count,
    query_model=WordCountParams,
    response_model=WordCountResponse,
    summary="Counts words in a text",
    description="Takes a text and returns the number of words in it.",
)


flock.serve(custom_endpoints=[img_url_route, word_count_route, yoda_route], chat=True)
