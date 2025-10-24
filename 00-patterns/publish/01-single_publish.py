import asyncio

from pydantic import BaseModel

from flock import Flock
from flock.registry import flock_type


@flock_type
class Idea(BaseModel):
    story_idea: str


@flock_type
class Movie(BaseModel):
    title: str
    genre: str
    director: str
    cast: list[str]
    plot_summary: str


@flock_type
class MovieScript(BaseModel):
    title: str
    acts: list[str]
    chapters: list[str]
    summary: str


flock = Flock()

# Single Publish
single_movie_master = flock.agent("single_movie_master").consumes(Idea).publishes(Movie)
single_script_master = flock.agent("single_script_master").consumes(Movie).publishes(MovieScript)


async def main():
    idea = Idea(story_idea="A romantic comedy set in a cat cafe")
    await flock.publish(idea)
    await flock.run_until_idle()


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
