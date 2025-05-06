"""
Purpose: Demonstrate how to use context lookups to access information across agents.

Use Case: Interactive Story Collaboration 📚 - Multiple agents collaborate to build
         a story together, each accessing different parts of the context.

Highlights:
- Access information from the context using special lookup syntax
- Reference outputs from other agents in the chain
- Use different lookup patterns to access specific pieces of information
- Show how context enables more complex agent interactions than simple chaining
"""

import os

from flock.cli.utils import print_header, print_subheader
from flock.core import Flock, FlockFactory
from flock.core.logging.formatters.themes import OutputTheme
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# --- Configuration ---
console = Console()
MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4o")
console.print(f"[grey50]Using model: {MODEL}[/grey50]")

# --- Create Flock Instance ---
flock = Flock(name="story_collaboration", model=MODEL, show_flock_banner=False)

# --------------------------------
# Context Lookup Rules Explained
# --------------------------------
print_header("Context Lookup Rules in Flock")
console.print("Flock provides special syntax for accessing information across agents:")
lookup_table = Table(title="Context Lookup Patterns")
lookup_table.add_column("Pattern", style="cyan")
lookup_table.add_column("Description", style="green")
lookup_table.add_column("Example", style="yellow")

lookup_table.add_row(
    "context",
    "Returns the entire context object",
    'input: "context | The full context"',
)
lookup_table.add_row(
    "context.property",
    "Returns a specific property from the context",
    'input: "context.story_theme | The theme of our story"',
)
lookup_table.add_row(
    "def.agent_name",
    "Returns the agent definition for the given agent",
    'input: "def.character_creator | The character creator agent definition"',
)
lookup_table.add_row(
    "agent_name",
    "Returns the most recent record from the agent's history",
    'input: "character_creator | The character creator\'s output"',
)
lookup_table.add_row(
    "agent_name.property",
    "Returns a specific property from an agent's state",
    'input: "character_creator.character_name | The name of our character"',
)
lookup_table.add_row(
    "property",
    "Searches history for the most recent value of a property",
    'input: "story_setting | The setting of our story"',
)

console.print(lookup_table)
console.print(
    "\nLet's see these in action with a collaborative story creation example!\n"
)

# --------------------------------
# Step 1: Story Theme Generator Agent
# --------------------------------
# This agent generates the initial theme and setting for our story
theme_agent = FlockFactory.create_default_agent(
    name="theme_generator",
    description="Generates creative story themes and settings.",
    input="genre: str | The genre of story to create",
    output="theme_generator_theme: str | The central theme of the story\n"
    "theme_generator_setting: str | The setting where the story takes place\n"
    "theme_generator_time_period: str | The time period of the story\n"
    "theme_generator_mood: str | The overall mood or tone",
    temperature=0.7,
    enable_rich_tables=True,
    output_theme=OutputTheme.monokai,
    wait_for_input=True,
)

# --------------------------------
# Step 2: Character Creator Agent
# --------------------------------
# This agent creates characters based on the theme and setting
# Note the use of context lookups in the input to access theme_agent's outputs
character_agent = FlockFactory.create_default_agent(
    name="character_creator",
    description="Creates compelling characters that fit the story theme and setting.",
    input="theme_generator_theme: str | The central theme of the story\n"
    "theme_generator_setting: str | The setting where the story takes place\n"
    "theme_generator_time_period: str | The time period of the story\n"
    "theme_generator_mood: str | The overall mood or tone",
    output="cc_protagonist: dict | The main character of the story\n"
    "cc_antagonist: dict | The opposing character or force\n"
    "cc_supporting_character: dict | An important supporting character",
    temperature=0.7,
    enable_rich_tables=True,
    output_theme=OutputTheme.dracula,
    wait_for_input=True,
)

# --------------------------------
# Step 3: Plot Outline Agent
# --------------------------------
# This agent creates a plot outline using both theme and character information
# Note how it accesses both theme_agent and character_agent outputs
plot_agent = FlockFactory.create_default_agent(
    name="plot_outliner",
    description="Creates a compelling plot outline based on the theme and characters.",
    input="theme_generator_theme: str | The theme from the theme generator\n"
    "theme_generator_setting: str | The setting from the theme generator\n"
    "cc_protagonist: dict | The protagonist character\n"
    "cc_antagonist: dict | The antagonist character",
    output="po_plot_points: list[str] | The main plot points in sequence\n"
    "po_conflict: str | The central conflict of the story\n"
    "po_resolution: str | How the story might resolve",
    temperature=0.7,
    enable_rich_tables=True,
    output_theme=OutputTheme.synthwave,
    wait_for_input=True,
)

# --------------------------------
# Step 4: Story Opener Agent
# --------------------------------
# This agent writes the opening paragraph of the story
# Note the different ways it accesses context from previous agents
opener_agent = FlockFactory.create_default_agent(
    name="story_opener",
    description="Writes an engaging opening paragraph for the story.",
    input="theme_generator.theme_generator_mood | The mood of the story\n"
    "theme_generator.theme_generator_setting | The setting of the story\n"
    "character_creator.cc_protagonist | The protagonist\n"
    "plot_outliner.po_plot_points | The plot points",
    output="so_opening_paragraph: str | The opening paragraph of the story\n"
    "so_narrative_voice: str | The narrative voice/perspective used",
    temperature=0.8,
    enable_rich_tables=True,
    output_theme=OutputTheme.aardvark_blue,
    wait_for_input=True,
)

# --------------------------------
# Step 5: Story Critic Agent
# --------------------------------
# This agent reviews the entire story development so far
# Note how it uses "context" to access everything at once
critic_agent = FlockFactory.create_default_agent(
    name="story_critic",
    description="Reviews the story elements and provides constructive feedback.",
    input="context | The entire context with all story elements",
    output="sc_strengths: list[str] | The strongest elements of the story so far\n"
    "sc_weaknesses: list[str] | Areas that could be improved\n"
    "sc_suggestions: list[str] | Specific suggestions for improvement",
    temperature=0.7,
    enable_rich_tables=True,
    output_theme=OutputTheme.fruity,
)

# --------------------------------
# Add agents to Flock
# --------------------------------
flock.add_agent(theme_agent)
flock.add_agent(character_agent)
flock.add_agent(plot_agent)
flock.add_agent(opener_agent)
flock.add_agent(critic_agent)


# --------------------------------
# Run the collaborative story creation
# --------------------------------
def run_story_collaboration(genre: str):
    """Run the collaborative story creation process with the given genre."""
    print_header(f"Collaborative Story Creation: {genre}")

    # Step 1: Generate theme and setting
    print_subheader("Step 1: Generating Theme and Setting")
    theme_result = flock.run(start_agent=theme_agent, input={"genre": genre})

    # Step 2: Create characters based on theme
    print_subheader("Step 2: Creating Characters")
    # We could manually pass the theme agent's outputs, but instead
    # we'll let the character agent use its input definition to pull them from context
    character_result = flock.run(start_agent=character_agent)

    # Step 3: Create plot outline based on theme and characters
    print_subheader("Step 3: Creating Plot Outline")
    # Again, the plot agent will pull what it needs from the context
    plot_result = flock.run(start_agent=plot_agent)

    # Step 4: Write the opening paragraph
    print_subheader("Step 4: Writing Opening Paragraph")
    opener_result = flock.run(start_agent=opener_agent)

    # Step 5: Get critique of the whole story development
    print_subheader("Step 5: Story Critique")
    critic_result = flock.run(start_agent=critic_agent)

    # Display the final story elements
    print_header("Final Story Elements")

    # Theme and Setting
    theme_panel = Panel(
        f"[bold]Theme:[/bold] {theme_result.theme_generator_theme}\n"
        f"[bold]Setting:[/bold] {theme_result.theme_generator_setting}\n"
        f"[bold]Time Period:[/bold] {theme_result.theme_generator_time_period}\n"
        f"[bold]Mood:[/bold] {theme_result.theme_generator_mood}",
        title="Theme and Setting",
        border_style="cyan",
    )
    console.print(theme_panel)

    # Characters
    character_table = Table(title="Characters")
    character_table.add_column("Role", style="cyan")
    character_table.add_column("Details", style="green")

    character_table.add_row("Protagonist", str(character_result.cc_protagonist))
    character_table.add_row("Antagonist", str(character_result.cc_antagonist))
    character_table.add_row(
        "Supporting Character", str(character_result.cc_supporting_character)
    )

    console.print(character_table)

    # Plot
    plot_panel = Panel(
        f"[bold]Conflict:[/bold] {plot_result.po_conflict}\n\n"
        f"[bold]Plot Points:[/bold]\n"
        + "\n".join(f"- {point}" for point in plot_result.po_plot_points)
        + "\n\n"
        f"[bold]Resolution:[/bold] {plot_result.po_resolution}",
        title="Plot Outline",
        border_style="magenta",
    )
    console.print(plot_panel)

    # Opening Paragraph
    opening_panel = Panel(
        opener_result.so_opening_paragraph + "\n\n"
        f"[italic]Narrative Voice: {opener_result.so_narrative_voice}[/italic]",
        title="Opening Paragraph",
        border_style="yellow",
    )
    console.print(opening_panel)

    # Critique
    critique_panel = Panel(
        "[bold]Strengths:[/bold]\n"
        + "\n".join(f"- {strength}" for strength in critic_result.sc_strengths)
        + "\n\n"
        "[bold]Weaknesses:[/bold]\n"
        + "\n".join(f"- {weakness}" for weakness in critic_result.sc_weaknesses)
        + "\n\n"
        "[bold]Suggestions:[/bold]\n"
        + "\n".join(f"- {suggestion}" for suggestion in critic_result.sc_suggestions),
        title="Story Critique",
        border_style="red",
    )
    console.print(critique_panel)

    return {
        "theme_result": theme_result,
        "character_result": character_result,
        "plot_result": plot_result,
        "opener_result": opener_result,
        "critic_result": critic_result,
    }


# --------------------------------
# Demonstrate Context Lookup Patterns
# --------------------------------
def show_context_lookup_examples(results):
    """Show examples of how the different context lookup patterns were used."""
    print_header("Context Lookup Examples")

    examples_table = Table(title="How Context Lookups Were Used")
    examples_table.add_column("Agent", style="cyan")
    examples_table.add_column("Lookup Pattern", style="green")
    examples_table.add_column("What It Accessed", style="yellow")

    examples_table.add_row(
        "character_creator",
        "theme_generator_theme",
        f"Theme: {results['theme_result'].theme_generator_theme}",
    )

    examples_table.add_row(
        "plot_outliner",
        "cc_protagonist",
        f"Protagonist: {str(results['character_result'].cc_protagonist)[:50]}...",
    )

    examples_table.add_row(
        "story_opener",
        "theme_generator.theme_generator_setting",
        f"Setting: {results['theme_result'].theme_generator_setting}",
    )

    examples_table.add_row(
        "story_critic", "context", "The entire context with all story elements"
    )

    console.print(examples_table)

    # Explanation of benefits
    print_subheader("Benefits of Context Lookups")
    console.print(
        "1. [bold]Flexibility:[/bold] Agents can access any information from any previous agent"
    )
    console.print(
        "2. [bold]Selective Access:[/bold] Agents can choose only the specific pieces of information they need"
    )
    console.print(
        "3. [bold]Reduced Redundancy:[/bold] No need to manually pass all outputs between agents"
    )
    console.print(
        "4. [bold]Easier Maintenance:[/bold] Adding new agents or changing outputs doesn't break the chain"
    )
    console.print(
        "5. [bold]Global Context:[/bold] Agents can access the entire context when needed for holistic analysis"
    )


# --------------------------------
# Main Execution
# --------------------------------
if __name__ == "__main__":
    # Run the collaborative story creation with a fantasy genre
    results = run_story_collaboration("science fiction")

    # Show examples of the context lookup patterns
    show_context_lookup_examples(results)

    print_header("Context Lookup Rules Summary")
    console.print("The lookup rules we demonstrated:")
    console.print(
        '- [bold]"property"[/bold]: Direct property access (e.g., theme_generator_theme)'
    )
    console.print(
        '- [bold]"agent_name.property"[/bold]: Access specific agent property (e.g., theme_generator.theme_generator_setting)'
    )
    console.print(
        '- [bold]"context"[/bold]: Access the entire context (used by the critic agent)'
    )

    console.print(
        "\nThese patterns enable complex agent interactions beyond simple chaining!"
    )

# --- YOUR TURN! ---
# 1. Try different lookup patterns:
#    - Modify the input of the opener_agent to use different lookup patterns
#    - For example, try using "po_conflict" instead of "plot_outliner.po_conflict"
#    - See if the agent can still find the information in the context
#
# 2. Add a new agent that needs information from multiple previous agents:
#    - Create a "story_illustrator" agent that needs character and setting details
#    - Use different lookup patterns to access this information
#    - See how context lookups make this easier than passing all the data manually
#
# 3. Try using "def.agent_name":
#    - Add an agent that uses "def.theme_generator" in its input
#    - This gives access to the theme_generator's definition (not its outputs)
#    - Use this to create a "meta" agent that analyzes how the story was created
#
# 4. Create a context-aware agent:
#    - Add a "story_reviser" agent that takes "context" as input
#    - Have it suggest revisions based on everything that's been generated
#    - See how it can synthesize information across all previous agents
#
# 5. Experiment with fallback behavior:
#    - Try referencing a property that doesn't exist in the context
#    - See how the system handles this and what fallback values it uses
