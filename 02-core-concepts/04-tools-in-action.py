# 02-core-concepts/04-tools-in-action-alt.py
"""
Purpose: Demonstrate how to create and use custom tools with Flock agents.

Use Case: Virtual Pet Tamagotchi 🐱 - Create a virtual pet that agents can interact with
         using custom tools to feed, play with, and check on the pet's status.

Highlights:
- Define custom tools with the @flock_tool decorator
- Show how agents can use tools to maintain state across interactions
- Demonstrate tool composition (using multiple tools together to solve a problem)
- Showcase how agents can reason about when and how to use tools
- Compare with what would be impossible in a stateless, single-prompt approach
"""

import os

from flock.cli.utils import print_header, print_subheader
from flock.core import Flock, FlockFactory
from rich.console import Console
from rich.table import Table
from tools.pet_tools import (
    buy_item,
    display_pet_status,
    feed_pet,
    get_mood_history,
    get_pet_status,
    perform_trick,
    play_with_pet,
    teach_trick,
)

# --- Configuration ---
console = Console()
MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4o")
console.print(f"[grey50]Using model: {MODEL}[/grey50]")


# --------------------------------
# Create the Pet Caretaker Agent
# --------------------------------
# Create a Flock instance
flock = Flock(name="virtual_pet", model=MODEL, show_flock_banner=False)

# Create the pet caretaker agent with access to all our custom tools
pet_agent = FlockFactory.create_default_agent(
    name="pet_caretaker",
    description="You are a helpful virtual pet caretaker assistant. You help users take care of their virtual pet by using the available tools. "
    "For the pet's attributes: hunger, happiness, and energy, the scale is 0-100 where 0 is the worst possible state "
    "(starving, very sad, completely exhausted) and 100 is the best possible state (completely full, very happy, fully energetic).",
    input="user_request: str | The user's request about their virtual pet",
    output="response: str | Your helpful response to the user's request",
    tools=[
        get_pet_status,
        feed_pet,
        play_with_pet,
        teach_trick,
        buy_item,
        get_mood_history,
        perform_trick,
    ],
    temperature=0.7,
    include_thought_process=True,  # Show the agent's reasoning
)

# Add the agent to the flock
flock.add_agent(pet_agent)


# --------------------------------
# Main Execution
# --------------------------------
def run_pet_example():
    """Run the virtual pet example."""
    print_header("🐱 Virtual Pet Tamagotchi Example 🐱")
    console.print(
        "This example demonstrates how agents can use custom tools to maintain state and perform complex interactions."
    )

    # Display initial pet status
    print_subheader("Initial Pet Status")
    display_pet_status(get_pet_status())

    # Example 1: Simple tool usage
    print_subheader("Example 1: Simple Tool Usage")
    console.print("[bold]User Request:[/bold] How is my pet doing?")

    result = flock.run(
        start_agent=pet_agent, input={"user_request": "How is my pet doing?"}
    )
    console.print(f"[bold]Agent Response:[/bold] {result.response}")

    # Example 2: Tool composition (using multiple tools together)
    print_subheader("Example 2: Tool Composition")
    console.print("[bold]User Request:[/bold] My pet seems unhappy, what should I do?")

    result = flock.run(
        start_agent=pet_agent,
        input={"user_request": "My pet seems unhappy, what should I do?"},
    )
    console.print(f"[bold]Agent Response:[/bold] {result.response}")

    # Example 3: Complex reasoning and tool chaining
    print_subheader("Example 3: Complex Reasoning and Tool Chaining")
    console.print(
        "[bold]User Request:[/bold] I want to teach my pet a new trick, but I'm not sure if it's ready."
    )

    result = flock.run(
        start_agent=pet_agent,
        input={
            "user_request": "I want to teach my pet a new trick, but I'm not sure if it's ready."
        },
    )
    console.print(f"[bold]Agent Response:[/bold] {result.response}")

    # Example 4: Handling sequential actions
    print_subheader("Example 4: Sequential Actions")
    console.print(
        "[bold]User Request:[/bold] Feed my pet, play with it using the toy mouse, and then check if it can learn to roll over."
    )

    result = flock.run(
        start_agent=pet_agent,
        input={
            "user_request": "Feed my pet, play with it using the toy mouse, and then check if it can learn to roll over."
        },
    )
    console.print(f"[bold]Agent Response:[/bold] {result.response}")

    # Display final pet status
    print_subheader("Final Pet Status")
    display_pet_status(get_pet_status())

    # Show comparison with traditional approaches
    print_header("Why This Requires an Agent Framework")
    console.print(
        "This example demonstrates several capabilities that would be difficult or impossible with traditional, stateless LLM prompting:"
    )

    comparison_table = Table(title="Agent Framework vs. Traditional Prompting")
    comparison_table.add_column("Capability", style="cyan")
    comparison_table.add_column("Agent Framework", style="green")
    comparison_table.add_column("Traditional Prompting", style="red")

    comparison_table.add_row(
        "State Management",
        "✓ Maintains pet state across interactions",
        "✗ Cannot maintain state between prompts",
    )
    comparison_table.add_row(
        "Tool Composition",
        "✓ Can use multiple tools in sequence based on reasoning",
        "✗ Limited to pre-defined tool sequences",
    )
    comparison_table.add_row(
        "Conditional Logic",
        "✓ Can make decisions based on tool outputs",
        "✗ Cannot adapt based on dynamic data",
    )
    comparison_table.add_row(
        "Iterative Processing",
        "✓ Can process lists and repeat tool calls",
        "✗ Cannot iterate through data effectively",
    )
    comparison_table.add_row(
        "Error Handling",
        "✓ Can retry or try alternative approaches",
        "✗ No built-in error recovery",
    )

    console.print(comparison_table)


if __name__ == "__main__":
    run_pet_example()

    # Interactive mode
    print_header("🐱 Interactive Pet Caretaker Mode 🐱")
    console.print("You can now interact directly with your virtual pet!")
    console.print("Type 'exit' or 'quit' to end the session.")
    console.print("Type 'status' to see your pet's current status.\n")

    # Display current pet status
    display_pet_status(get_pet_status())

    while True:
        try:
            # Get user input
            user_request = input(
                "\n[bold cyan]What would you like to do with your pet?[/bold cyan] "
            )

            # Check for exit command
            if user_request.lower() in ["exit", "quit"]:
                console.print(
                    "[bold]Thank you for taking care of your virtual pet! Goodbye![/bold]"
                )
                break

            # Check for status command
            if user_request.lower() == "status":
                display_pet_status(get_pet_status())
                continue

            # Process the user request with the agent
            console.print("[bold]Processing your request...[/bold]")
            result = flock.run(
                start_agent=pet_agent, input={"user_request": user_request}
            )

            # Display the agent's response
            console.print(f"[bold green]Agent Response:[/bold green] {result.response}")

            # Show updated pet status after each interaction
            console.print("\n[bold]Updated Pet Status:[/bold]")
            display_pet_status(get_pet_status())

        except KeyboardInterrupt:
            console.print("\n[bold]Session interrupted. Goodbye![/bold]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            console.print("Please try again.")

# --- YOUR TURN! ---
# 1. Add a new tool:
#    - Create a new @flock_tool function like "give_bath" or "take_for_walk"
#    - Make it affect the pet's stats in interesting ways
#    - Add it to the pet_agent's tools list
#
# 2. Create a multi-step interaction:
#    - Try asking the agent to optimize your pet's happiness in as few steps as possible
#    - See if it can reason through the most efficient sequence of tool calls
#
# 3. Add a new pet attribute:
#    - Add a "health" or "cleanliness" attribute to the PET dictionary
#    - Update the relevant tools to affect this attribute
#    - See how the agent adapts to the new attribute
#
# 4. Create a challenging scenario:
#    - Set some of the pet's stats to extreme values (very hungry, very unhappy)
#    - Ask the agent to help you restore the pet to a happy state
#    - See if it prioritizes the most critical needs first
#
# 5. Implement a daily routine:
#    - Ask the agent to create an optimal daily care routine for your pet
#    - Have it explain which tools to use and in what order
#    - See if it considers the time-based changes to hunger and happiness
