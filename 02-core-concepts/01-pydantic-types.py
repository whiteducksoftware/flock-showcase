# 02-core-concepts/01-pydantic-types.py
"""
Purpose: Demonstrate using Pydantic models to define structured output.

Use Case: Fantasy RPG Character Generator 🧙‍♂️ - Generate structured fantasy character data.

Highlights:
- Define a Pydantic model (`FantasyCharacter`) with typed fields.
- Use the `@flock_type` decorator to register the custom type.
- Define a Flock agent whose `output` signature references the Pydantic model (`list[FantasyCharacter]`).
- Flock automatically instructs the LLM to generate data matching the Pydantic schema.
- The result object contains actual instances of the Pydantic model.
"""

import os
from pprint import pprint  # Using pprint for cleaner dict/list printing
from typing import Literal

from flock.cli.utils import print_header, print_subheader, print_warning
from flock.core import Flock, FlockFactory
from flock.core.flock_registry import (
    flock_type,  # Decorator for registering custom types
)
from pydantic import BaseModel, Field  # Import Pydantic components
from rich.console import Console

# --- Configuration ---
console = Console()
MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4o")
console.print(f"[grey50]Using model: {MODEL}[/grey50]")


# --------------------------------
# Define the Pydantic data model
# --------------------------------
# Use the @flock_type decorator so Flock knows about this custom class
# and can use it in signatures and handle serialization/deserialization.
# Check the cookbook for an example of handling images as well in 'working_with_images.py'
@flock_type
class FantasyCharacter(BaseModel):
    """Data model for fantasy RPG character information.
    Docstrings and Field descriptions can help guide the LLM.
    """

    name: str = Field(..., description="A creative fantasy character name.")
    race: Literal["human", "elf", "dwarf", "orc", "halfling"] = Field(
        ..., description="The character's race."
    )
    class_type: Literal["warrior", "mage", "rogue", "cleric", "ranger"] = Field(
        ..., description="The character's class."
    )
    level: int = Field(..., description="Character level")
    strength: int = Field(..., description="Strength stat")
    dexterity: int = Field(..., description="Dexterity stat")
    constitution: int = Field(..., description="Constitution stat")
    intelligence: int = Field(..., description="Intelligence stat")
    wisdom: int = Field(..., description="Wisdom stat")
    charisma: int = Field(..., description="Charisma stat")
    weapons: list[str] = Field(
        ..., description="A list of weapons the character carries."
    )
    backstory: str = Field(
        ..., description="A brief, engaging backstory (2-3 sentences)."
    )
    motivation: str = Field(
        ..., description="The character's motivation for their adventuring."
    )
    alignment: str = Field(
        ...,
        description="Character's moral alignment",
    )


# --------------------------------
# Create a new Flock instance
# --------------------------------
flock = Flock(name="pydantic_example", model=MODEL, show_flock_banner=False)

# --------------------------------
# Define the Agent using the Pydantic type
# --------------------------------
# The agent is responsible for generating a list of fantasy characters.
# Input: "number_of_characters" (string or int).
# Output: "character_list" which MUST be a list of FantasyCharacter objects.
character_agent = FlockFactory.create_default_agent(
    name="character_agent",
    description="Generates fantasy RPG character profiles for a specified number of characters.",
    input="number_of_characters: int | The number of fantasy character profiles to generate.",
    # Crucially, the output type refers to our registered Pydantic model:
    output="character_list: list[FantasyCharacter] | A list containing the generated character profiles.",
    temperature=0.8,  # Increase temperature slightly for more varied profiles
)
flock.add_agent(character_agent)


# --------------------------------
# Run the Flock
# --------------------------------
print_header("Generating Fantasy RPG Character Profiles")
num_to_generate = 2  # Let's generate just 2 for a quicker example
console.print(f"Requesting {num_to_generate} character profiles...")

try:
    result = flock.run(
        start_agent="character_agent",
        input={"number_of_characters": num_to_generate},
    )

    # --------------------------------
    # Display the results
    # --------------------------------
    print_subheader("Generated Character Profiles")
    if hasattr(result, "character_list") and isinstance(result.character_list, list):
        console.print(f"Received {len(result.character_list)} character profiles:")

        for i, character in enumerate(result.character_list):
            print_subheader(f"Character {i + 1}")
            # Access attributes directly - they are FantasyCharacter instances!
            if isinstance(character, FantasyCharacter):
                console.print(f"  [cyan]Name:[/cyan] {character.name}")
                console.print(f"  [cyan]Race:[/cyan] {character.race}")
                console.print(f"  [cyan]Class:[/cyan] {character.class_type}")
                console.print(f"  [cyan]Level:[/cyan] {character.level}")
                console.print(f"  [cyan]Alignment:[/cyan] {character.alignment}")
                console.print("\n  [cyan]Stats:[/cyan]")
                console.print(f"    Strength: {character.strength}")
                console.print(f"    Dexterity: {character.dexterity}")
                console.print(f"    Constitution: {character.constitution}")
                console.print(f"    Intelligence: {character.intelligence}")
                console.print(f"    Wisdom: {character.wisdom}")
                console.print(f"    Charisma: {character.charisma}")
                console.print(f"\n  [cyan]Weapons:[/cyan] {character.weapons}")
                console.print(f"  [cyan]Backstory:[/cyan] {character.backstory}\n")
                # Verify the type
                console.print(f"  [grey50](Object Type: {type(character)})[/grey50]\n")
            else:
                print_warning(
                    f"Item {i + 1} in list is not a FantasyCharacter object: {type(character)}"
                )
                pprint(character)  # Print raw if not expected type
    else:
        print_warning(
            "Agent did not return the expected 'character_list' field or it wasn't a list."
        )
        print_warning("Raw result:")
        pprint(result)  # Print the raw result if structure is wrong

except Exception as e:
    print_warning(f"Agent run failed: {e}")
    print_warning("Please ensure your API key is set and the model is accessible.")


# --- YOUR TURN! ---
# 1. Modify the `FantasyCharacter` Pydantic model:
#    - Add a new field, e.g., `homeland: str = Field(..., description="The character's place of origin")`.
#    - Change an existing field's type, e.g., make `level` a `float` to represent characters with partial levels.
#
#    The LLM will probably try to generate values fitting Dungeons and Dragons rules. Like all the stats being between 3 and 18.
#    - Add validation to a field:
#      For example, expand level range with Field(gt=20, le=100)
#      Try the following for weapons: Field(..., min_items=1, max_items=4, description="Between 1-4 weapons the character carries")
#      Try the following for alignment: Field(..., pattern=r'^(Lawful|Neutral|Chaotic) (Good|Neutral|Evil)$')
#      Remove everything good in the alignment field to make a 'bad character' generator.
#    - Try adding following properties to the model:
#      - character_id: str = Field(..., description="A unique identifier for the character.", pattern=r"(?:([+]\d{1,4})[-.\s]?)?(?:[(](\d{1,3})[)][-.\s]?)?(\d{1,4})[-.\s]?(\d{1,4})[-.\s]?(\d{1,9})")
#      What kind of format does the LLM use for the character_id?
#    Run the script again. Does the LLM adapt to generate the new field or respect the new type/validation?
#
# 2. Change the `output` signature of the `character_agent`:
#    - Instead of `List[FantasyCharacter]`, try asking for just one: `the_character: FantasyCharacter`
#      (You'll need to adjust the result processing code accordingly).
#    - Try asking for a dictionary mapping names to profiles: `characters_by_name: Dict[str, FantasyCharacter]`
#      (Again, adjust the result processing).
#
# 3. Introduce a nested Pydantic model:
#    - Define a new `@flock_type class Equipment(BaseModel): armor: str; magical_items: list[str]`.
#    - Add `equipment: Equipment` as a field to `FantasyCharacter`.
#    Run the script. Does Flock handle generating the nested structure?
