from dataclasses import dataclass
from pprint import pprint
from typing import Literal

from flock.core import Flock, FlockFactory
from flock.core.flock_registry import flock_type
from pydantic import BaseModel

# --------------------------------
# Define the data model for a random person
# --------------------------------
@flock_type
class RandomPerson(BaseModel):
    """Data model for random person information."""
    name: str
    age: int
    gender: Literal["female", "male"]
    job: str
    favorite_movie: str  
    short_bio: str


# --------------------------------   
# Create a new Flock instance
# --------------------------------
flock = Flock()

# --------------------------------
# Define the Random User List Agent
# --------------------------------
# This agent ("people_agent") is responsible for generating a list of random users.
# It requires the input "amount_of_people" and produces an output "random_user_list" 
# which is a list of RandomPerson objects.
people_agent = FlockFactory.create_default_agent(
    name="people_agent",
    input="amount_of_people",
    output="random_user_list: list[RandomPerson]",
)
flock.add_agent(people_agent)


# --------------------------------
# Run the loaded Flock
# --------------------------------
# We can now run the loaded Flock, which uses the dynamically recreated RandomPerson type
result = flock.run(
    start_agent="people_agent",
    input={"amount_of_people": "3"},  # Generating just 3 for brevity
)

# --------------------------------
# Display the results
# --------------------------------
print(f"\nGenerated {len(result.random_user_list)} random people:")
for person in result.random_user_list[:2]:  # Show just the first 2 for brevity
    print(f"\nName: {person.name}")
    print(f"Age: {person.age}")
    print(f"Gender: {person.gender}")
    print(f"Job: {person.job}")
    print(f"Favorite Movie: {person.favorite_movie}")
    print(f"Bio: {person.short_bio[:50]}..." if len(person.short_bio) > 50 else f"Bio: {person.short_bio}")



