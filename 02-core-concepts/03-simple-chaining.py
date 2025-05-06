# 02-core-concepts/03-simple-chaining-alt.py
"""
Purpose: Demonstrate how to chain multiple agents together to solve complex tasks.

Use Case: Fantasy Character Adventure Generator 🧙‍♂️🐉 - Create a character,
         generate an adventure, and narrate an epic conclusion.

Highlights:
- Chain multiple specialized agents together to build a complete workflow
- Each agent focuses on a specific task and passes its output to the next agent
- Show different ways to connect agents (default router, LLM router)
- Demonstrate how complex creative tasks can be broken down into manageable steps
"""

import os

from flock.cli.utils import print_header, print_subheader, print_success, print_warning
from flock.core import Flock, FlockFactory
from flock.core.logging.formatters.themes import OutputTheme
from flock.routers.default.default_router import DefaultRouterConfig
from rich.console import Console
from rich.panel import Panel

# --- Configuration ---
console = Console()
MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4o")
console.print(f"[grey50]Using model: {MODEL}[/grey50]")

# --- Create Flock Instance ---
flock = Flock(
    name="adventure_generator",
    model=MODEL,
    show_flock_banner=False,
)

# --------------------------------
# Step 1: Create Character Generator Agent
# --------------------------------
# This agent creates a fantasy character based on user preferences
character_agent = FlockFactory.create_default_agent(
    name="character_generator",
    description="Creates detailed fantasy characters based on user preferences.",
    input="character_type: str | The general type of character the user wants to create",
    output="character_name: str | The character's full name, "
    "character_race: str | The character's fantasy race, "
    "character_class: str | The character's profession or class, "
    "character_background: str | A brief backstory for the character, "
    "character_traits: list[str] | Three to five personality traits, "
    "character_abilities: list[str] | Special abilities or skills",
    temperature=0.7,  # Higher temperature for more creative characters
    enable_rich_tables=True,
    output_theme=OutputTheme.batman,
    use_cache=False,  # Disable caching for this agent
    wait_for_input=True,  # Pause after generating the character
)

# --------------------------------
# Step 2: Create Adventure Generator Agent
# --------------------------------
# This agent creates an adventure scenario based on the character
adventure_agent = FlockFactory.create_default_agent(
    name="adventure_generator",
    description="Creates an adventure scenario tailored to a specific character.",
    input="character_name: str | The character's name,"
    "character_race: str | The character's race,"
    "character_class: str | The character's class,"
    "character_background: str | The character's backstory,"
    "character_abilities: list[str] | The character's special abilities",
    output="adventure_title: str | An epic title for the adventure,"
    "adventure_setting: str | Where the adventure takes place,"
    "adventure_quest: str | The main objective or quest,"
    "adventure_challenges: list[str] | Three to five challenges the character will face,"
    "adventure_allies: list[str] | One or two potential allies,"
    "adventure_antagonist: str | The main antagonist or obstacle",
    temperature=0.7,
    enable_rich_tables=True,
    output_theme=OutputTheme.dracula,
    wait_for_input=True,  # Pause after generating the adventure
)

# --------------------------------
# Step 3: Create Story Conclusion Agent
# --------------------------------
# This agent creates an epic conclusion to the adventure
conclusion_agent = FlockFactory.create_default_agent(
    name="conclusion_generator",
    description="Creates an epic conclusion to a character's adventure.",
    input="character_name: str | The character's name,"
    "character_race: str | The character's race,"
    "character_class: str | The character's class,"
    "character_abilities: list[str] | The character's special abilities,"
    "adventure_title: str | The adventure's title,"
    "adventure_setting: str | The adventure's setting,"
    "adventure_quest: str | The main quest,"
    "adventure_challenges: list[str] | The challenges faced,"
    "adventure_allies: list[str] | The character's allies,"
    "adventure_antagonist: str | The main antagonist",
    output="epic_conclusion: str | A dramatic and satisfying conclusion to the adventure,"
    "character_growth: str | How the character has changed or grown,"
    "sequel_hook: str | A teaser for a potential future adventure",
    temperature=0.8,  # Even higher temperature for a creative conclusion
    enable_rich_tables=True,
    output_theme=OutputTheme.synthwave,
)

# --------------------------------
# Chain the Agents Together
# --------------------------------
print_subheader("Agent Chaining Setup")
console.print("[bold]Setting up agent chain:[/bold]")
console.print("Character Generator → Adventure Generator → Conclusion Generator")

# Method 1: Using Default Router (simple, deterministic chaining)
console.print("\n[bold]Chaining Method:[/bold] Default Router (deterministic)")
character_agent.add_component(
    config_instance=DefaultRouterConfig(hand_off=adventure_agent.name),
    component_name="adventure_router",
)

adventure_agent.add_component(
    config_instance=DefaultRouterConfig(hand_off=conclusion_agent.name),
    component_name="conclusion_router",
)

# Alternative Method (commented out): Using LLM Router
# This would let the LLM decide which agent to call next based on context
# character_agent.handoff_router = LLMRouter(config=LLMRouterConfig(with_output=True))
# adventure_agent.handoff_router = LLMRouter(config=LLMRouterConfig(with_output=True))

# --------------------------------
# Add Agents to Flock
# --------------------------------
flock.add_agent(character_agent)
flock.add_agent(adventure_agent)
flock.add_agent(conclusion_agent)


# --------------------------------
# Run the Agent Chain
# --------------------------------
def run_adventure_generator(character_type):
    """Run the full agent chain to generate a character adventure."""
    print_header(f"Generating Adventure for {character_type.title()} Character")

    try:
        # Start with the character generator and the chain will continue automatically
        result = flock.run(
            start_agent=character_agent,
            input={"character_type": character_type},
        )

        # Display the final conclusion
        if hasattr(result, "epic_conclusion"):
            print_success("Adventure Complete!")

            conclusion_panel = Panel(
                result.epic_conclusion,
                title=f"The Conclusion of {result.character_name}'s Adventure",
                border_style="green",
            )
            console.print(conclusion_panel)

            growth_panel = Panel(
                result.character_growth, title="Character Growth", border_style="blue"
            )
            console.print(growth_panel)

            sequel_panel = Panel(
                result.sequel_hook, title="Next Adventure Hook", border_style="yellow"
            )
            console.print(sequel_panel)

            return result
        else:
            print_warning("The adventure chain did not complete as expected")
            return result

    except Exception as e:
        print_warning(f"Adventure generation failed: {e}")
        print_warning("Ensure your API key is set and the model is accessible.")
        return None


# --------------------------------
# Main Execution
# --------------------------------
if __name__ == "__main__":
    # Example character type
    example_character = "wizard"
    run_adventure_generator(example_character)

    print_header("How Agent Chaining Works")
    console.print(
        "1. The [bold]Character Generator[/bold] creates a detailed character"
    )
    console.print(
        "2. Its output is automatically passed to the [bold]Adventure Generator[/bold]"
    )
    console.print(
        "3. The adventure details are then passed to the [bold]Conclusion Generator[/bold]"
    )
    console.print("4. Each agent specializes in one part of the creative process")
    console.print(
        "\nThis demonstrates how complex tasks can be broken down into specialized agents,"
    )
    console.print(
        "each handling a specific subtask while passing context through the chain."
    )

# --- YOUR TURN! ---
# 1. Try with different character types:
#    - Change the example_character variable to "rogue", "paladin", "druid", etc.
#    - See how the entire adventure changes based on the initial input
#
# 2. Modify the agent chain:
#    - Add a new agent between Adventure and Conclusion (e.g., "battle_scene_generator")
#    - Update the chaining to include your new agent
#    - Adjust the inputs/outputs to pass the necessary information
#
# 3. Try different routing methods:
#    - Uncomment the LLMRouter lines and comment out the DefaultRouter lines
#    - This lets the LLM decide which agent to call next based on context
#    - Add a new agent that isn't in the main chain and see if the LLM router ever chooses it
#
# 4. Create a branching chain:
#    - Add two different conclusion agents (e.g., "happy_ending" and "tragic_ending")
#    - Use the LLM router to decide which ending to generate based on the adventure
#    - Hint: You'll need to define criteria for the router to consider
#
# 5. Add memory to the chain:
#    - Modify the agents to accept and pass along a "previous_adventures" parameter
#    - Create a character with multiple adventures that reference past events
