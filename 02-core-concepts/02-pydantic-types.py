# 02-core-concepts/02-pydantic-types.py
"""
Purpose: Demonstrate using Pydantic models to define structured output.

Use Case: Fantasy Character Sheet Generator 🧙‍♂️ - Generate structured character data.

Highlights:
- Define a Pydantic model (`RandomPerson`) with typed fields.
- Use the `@flock_type` decorator to register the custom type.
- Define a Flock agent whose `output` signature references the Pydantic model (`list[RandomPerson]`).
- Flock automatically instructs the LLM to generate data matching the Pydantic schema.
- The result object contains actual instances of the Pydantic model.
"""

import os
from pprint import pprint # Using pprint for cleaner dict/list printing
from typing import Literal
from pydantic import BaseModel, Field # Import Pydantic components

from flock.core import Flock, FlockFactory
from flock.core.flock_registry import flock_type # Decorator for registering custom types
from rich.console import Console

from flock.cli.utils import print_header, print_subheader, print_warning

# --- Configuration ---
console = Console()
MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4o")
console.print(f"[grey50]Using model: {MODEL}[/grey50]")


# --------------------------------
# Define the Pydantic data model
# --------------------------------
# Use the @flock_type decorator so Flock knows about this custom class
# and can use it in signatures and handle serialization/deserialization.
@flock_type
class RandomPerson(BaseModel):
    """Data model for random person information.
    Docstrings and Field descriptions can help guide the LLM.
    """
    first_name: str = Field(..., description="A creative first name.")
    last_name: str = Field(..., description="A creative last name. Written in all caps.")
    age: int = Field(..., description="An age between 18 and 80.")
    gender: Literal["female", "male", "non-binary"] # Use Literal for specific choices
    job: str = Field(..., description="A plausible occupation.")
    favorite_movies: list[str] = Field(..., description="A list of real or plausible movie titles.")
    short_bio: str = Field(..., description="A brief, engaging biography (2-3 sentences).")
    lucky_number: int = Field(..., description="A lucky number between 1 and 100.")
    phone_number: str = Field(..., description="A phone number.")




# --------------------------------
# Create a new Flock instance
# --------------------------------
flock = Flock(name="pydantic_example", model=MODEL, show_flock_banner=False)

# --------------------------------
# Define the Agent using the Pydantic type
# --------------------------------
# The agent is responsible for generating a list of random users.
# Input: "amount_of_people" (string or int).
# Output: "random_user_list" which MUST be a list of RandomPerson objects.
people_agent = FlockFactory.create_default_agent(
    name="people_agent",
    description="Generates fictional profiles for a specified number of people.",
    input="amount_of_people: int | The number of random people profiles to generate.",
    # Crucially, the output type refers to our registered Pydantic model:
    output="random_user_list: list[RandomPerson] | A list containing the generated person profiles.",
    temperature=0.8 # Increase temperature slightly for more varied profiles
)
flock.add_agent(people_agent)


# --------------------------------
# Run the Flock
# --------------------------------
print_header("Generating Random Person Profiles")
num_to_generate = 2 # Let's generate just 2 for a quicker example
console.print(f"Requesting {num_to_generate} profiles...")

try:
    result = flock.run(
        start_agent="people_agent",
        input={"amount_of_people": num_to_generate},
    )

    # --------------------------------
    # Display the results
    # --------------------------------
    print_subheader("Generated Profiles")
    if hasattr(result, 'random_user_list') and isinstance(result.random_user_list, list):
        console.print(f"Received {len(result.random_user_list)} profiles:")

        for i, person in enumerate(result.random_user_list):
            print_subheader(f"Profile {i+1}")
            # Access attributes directly - they are RandomPerson instances!
            if isinstance(person, RandomPerson):
                console.print(f"  [cyan]Name:[/cyan] {person.first_name} {person.last_name}")
                console.print(f"  [cyan]Age:[/cyan] {person.age}")
                console.print(f"  [cyan]Gender:[/cyan] {person.gender}")
                console.print(f"  [cyan]Job:[/cyan] {person.job}")
                console.print(f"  [cyan]Favorite Movies:[/cyan] {person.favorite_movies}")
                console.print(f"  [cyan]Phone Number:[/cyan] {person.phone_number}")
                console.print(f"  [cyan]Lucky Number:[/cyan] {person.lucky_number}")
                console.print(f"  [cyan]Bio:[/cyan] {person.short_bio}\n")
                # Verify the type
                console.print(f"  [grey50](Object Type: {type(person)})[/grey50]\n")
            else:
                 print_warning(f"Item {i+1} in list is not a RandomPerson object: {type(person)}")
                 pprint(person) # Print raw if not expected type
    else:
        print_warning("Agent did not return the expected 'random_user_list' field or it wasn't a list.")
        print_warning("Raw result:")
        pprint(result) # Print the raw result if structure is wrong

except Exception as e:
    print_warning(f"Agent run failed: {e}")
    print_warning("Please ensure your API key is set and the model is accessible.")


# --- YOUR TURN! ---
# 1. Modify the `RandomPerson` Pydantic model (lines 21-31):
#    - Add a new field, e.g., `city: str = Field(..., description="A plausible city name")`.
#    - Change an existing field's type, e.g., make `age` a `float`.
#    - Add validation to a field (e.g., using Pydantic's `@validator` or `Field(gt=0)` for age).
#    For example generate only people over 61 but under 100 and a multiple of 3 with Field(gt=61,le=100, multiple_of=3)
#    Try the following for phone numbers: Field(..., pattern=r'(?:([+]\d{1,4})[-.\s]?)?(?:[(](\d{1,3})[)][-.\s]?)?(\d{1,4})[-.\s]?(\d{1,4})[-.\s]?(\d{1,9})')
#    Try the following for movies: Field(..., min_length=3, max_length=5)
#    Run the script again. Does the LLM adapt to generate the new field or respect the new type/validation?
#
# 2. Change the `output` signature of the `people_agent` (line 49):
#    - Instead of `List[RandomPerson]`, try asking for just one: `the_person: RandomPerson`
#      (You'll need to adjust the result processing code lines 66-81 accordingly).
#    - Try asking for a dictionary mapping names to profiles: `profiles_by_name: Dict[str, RandomPerson]`
#      (Again, adjust the result processing).
#
# 3. Introduce a nested Pydantic model:
#    - Define a new `@flock_type class Address(BaseModel): street: str; city: str`.
#    - Add `address: Address` as a field to `RandomPerson`.
#    Run the script. Does Flock handle generating the nested structure?