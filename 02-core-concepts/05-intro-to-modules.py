"""Purpose: Demonstrate how to create and use modules in Flock agents.

Use Case: Virtual Pet Diary 📔 - Create a module that records significant events
         in your virtual pet's life, creating a personalized diary over time.

Highlights:
- Create a custom module with the @flock_component decorator
- Use module hooks like on_post_evaluate to capture agent interactions
- Store and retrieve persistent data across sessions
- Enhance agent capabilities without modifying core agent logic
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from flock.core import Flock, FlockAgent, FlockContext, FlockFactory
from flock.core.flock_module import FlockModule, FlockModuleConfig
from flock.core.flock_registry import flock_component
from flock.core.logging.logging import get_logger
from pydantic import Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from tools.pet_diary import add_diary_note, get_pet_diary
from tools.pet_tools import (
    buy_item,
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

logger = get_logger("pet_diary")


# --------------------------------
# Pet Diary Module Configuration
# --------------------------------
class PetDiaryModuleConfig(FlockModuleConfig):
    """Configuration for the Pet Diary Module that records significant events
    in a virtual pet's life.
    """

    diary_file: str = Field(
        default="pet_diary.json",
        description="The file to store the pet's diary entries.",
    )

    pet_name: str = Field(
        default="Pixel", description="The name of the pet for diary entries."
    )

    max_entries: int = Field(
        default=100, description="Maximum number of diary entries to keep."
    )


# --------------------------------
# Pet Diary Module Implementation
# --------------------------------
@flock_component(config_class=PetDiaryModuleConfig)
class PetDiaryModule(FlockModule):
    """A module that records significant events in a virtual pet's life,
    creating a personalized diary over time.
    """

    name: str = "pet_diary"
    config: PetDiaryModuleConfig = PetDiaryModuleConfig()
    diary_entries: list[dict] = []

    def __init__(self, name: str, config: PetDiaryModuleConfig):
        super().__init__(name=name, config=config)
        self.diary_entries = self._load_diary()

    def _load_diary(self) -> list[dict]:
        """Load diary entries from file or create empty diary."""
        diary_path = Path(self.config.diary_file)
        if diary_path.exists():
            try:
                with open(diary_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Error loading diary: {e}. Creating new diary.")
                return []
        return []

    def _save_diary(self) -> None:
        """Save diary entries to file."""
        with open(self.config.diary_file, "w") as f:
            json.dump(self.diary_entries, f, indent=2)

    def add_entry(
        self, event_type: str, description: str, details: dict = None
    ) -> None:
        """Add a new diary entry.

        Args:
            event_type: Type of event (e.g., "feeding", "playing", "milestone")
            description: Description of the event
            details: Additional details about the event
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "description": description,
            "details": details or {},
        }

        self.diary_entries.append(entry)

        # Trim diary if it exceeds max entries
        if len(self.diary_entries) > self.config.max_entries:
            self.diary_entries = self.diary_entries[-self.config.max_entries :]

        self._save_diary()
        logger.info(f"Added diary entry: {description}")

    def get_recent_entries(self, count: int = 5) -> list[dict]:
        """Get the most recent diary entries."""
        return self.diary_entries[-count:] if self.diary_entries else []

    def get_entries_by_type(self, event_type: str) -> list[dict]:
        """Get diary entries of a specific type."""
        return [
            entry for entry in self.diary_entries if entry["event_type"] == event_type
        ]

    # --------------------------------
    # Flock Module Integration Hooks
    # --------------------------------
    async def on_initialize(
        self,
        agent: FlockAgent,
        inputs: dict[str, Any],
        context: FlockContext | None = None,
    ):
        """Called when the agent is initialized."""
        # Add recent diary entries to the agent's context
        recent_entries = self.get_recent_entries(3)
        if recent_entries:
            formatted_entries = "\n".join(
                [
                    f"- {datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')}: {entry['description']}"
                    for entry in recent_entries
                ]
            )

            # Enhance the agent's description with recent diary entries
            agent.description = (
                f"{agent.description}\n\n"
                f"Recent events in {self.config.pet_name}'s diary:\n{formatted_entries}"
            )

            logger.info("Added recent diary entries to agent context")

    async def on_post_evaluate(
        self,
        agent: Any,
        inputs: dict[str, Any],
        context: FlockContext | None = None,
        result: dict[str, Any] | None = None,
    ):
        """Called after the agent is evaluated."""
        if not result:
            return

        user_request = inputs.get("user_request", "")
        response = result.get("response", "")

        # Analyze the interaction to detect significant events
        self._process_interaction(user_request, response, result)

    def _process_interaction(
        self, user_request: str, response: str, result: dict[str, Any]
    ) -> None:
        """Process agent interaction to detect significant events.

        This looks at the tools called and response to determine if something
        diary-worthy happened.
        """
        # Access the agent's thought process if available
        thought_process = result.get("thought_process", "")

        # Check for feeding events
        if "feed_pet" in thought_process or "fed" in response.lower():
            # Extract what the pet was fed
            food_items = [
                "basic kibble",
                "premium kibble",
                "gourmet fish",
                "treat",
            ]
            fed_item = next(
                (item for item in food_items if item in response.lower()),
                "food",
            )

            self.add_entry(
                event_type="feeding",
                description=f"{self.config.pet_name} was fed {fed_item}.",
                details={"food": fed_item},
            )

        # Check for playing events
        if "play_with_pet" in thought_process or "played" in response.lower():
            play_activities = [
                "toy mouse",
                "ball of yarn",
                "laser pointer",
                "feather wand",
                "petting",
                "chase",
            ]
            activity = next(
                (act for act in play_activities if act in response.lower()),
                "toys",
            )

            self.add_entry(
                event_type="playing",
                description=f"{self.config.pet_name} played with {activity}.",
                details={"activity": activity},
            )

        # Check for learning new tricks
        if "teach_trick" in thought_process and "learned" in response.lower():
            trick_words = ["sit", "paw", "roll", "speak", "jump", "trick"]
            trick = next(
                (word for word in trick_words if word in response.lower()),
                "a new trick",
            )

            self.add_entry(
                event_type="milestone",
                description=f"{self.config.pet_name} learned how to {trick}!",
                details={"trick": trick},
            )

        # Check for mood changes
        mood_words = ["happy", "sad", "hungry", "tired", "ecstatic", "content"]
        if any(mood in response.lower() for mood in mood_words):
            current_mood = next(
                (mood for mood in mood_words if mood in response.lower()),
                "different",
            )

            # Only record significant mood changes
            if current_mood in ["ecstatic", "sad", "hungry"]:
                self.add_entry(
                    event_type="mood",
                    description=f"{self.config.pet_name} is feeling {current_mood} today.",
                    details={"mood": current_mood},
                )

        # Check for new items
        if "buy_item" in thought_process or "purchased" in response.lower():
            item_words = [
                "toy",
                "food",
                "treat",
                "kibble",
                "mouse",
                "yarn",
                "pointer",
                "wand",
            ]
            item = next(
                (word for word in item_words if word in response.lower()),
                "something new",
            )

            self.add_entry(
                event_type="shopping",
                description=f"You bought {item} for {self.config.pet_name}.",
                details={"item": item},
            )


# --------------------------------
# Create the Pet Agent with Diary
# --------------------------------
async def run_pet_diary_example():
    """Run the pet diary module example."""
    console.print(
        Panel.fit(
            "🐱 Virtual Pet Diary Module Example 🐱\n\n"
            "This example demonstrates how to create and use modules in Flock agents.\n"
            "The Pet Diary Module automatically records significant events in your pet's life.",
            title="Pet Diary Module",
            border_style="cyan",
        )
    )

    # Create a Flock instance
    flock = Flock(
        name="virtual_pet_with_diary",
        model=MODEL,
        show_flock_banner=False,
    )

    # Create the pet caretaker agent
    pet_agent = FlockFactory.create_default_agent(
        name="pet_caretaker",
        description=(
            "You are a helpful virtual pet caretaker assistant. "
            "You help users take care of their virtual pet by using the available tools. "
            "For the pet's attributes: hunger, happiness, and energy, the scale is 0-100 "
            "where 0 is the worst possible state (starving, very sad, completely exhausted) "
            "and 100 is the best possible state (completely full, very happy, fully energetic)."
        ),
        input="user_request: str | The user's request about their virtual pet",
        output="response: str | Your helpful response to the user's request",
        tools=[
            get_pet_diary,
            add_diary_note,
            get_pet_status,
            feed_pet,
            play_with_pet,
            teach_trick,
            buy_item,
            get_mood_history,
            perform_trick,
        ],
        temperature=0.7,
        include_thought_process=True,
    )

    # Add the Pet Diary Module to the agent
    pet_diary_config = PetDiaryModuleConfig(
        pet_name="Pixel", diary_file="pet_diary.json"
    )
    pet_agent.add_component(
        config_instance=pet_diary_config, component_name="pet_diary"
    )

    # Add the agent to the flock
    flock.add_agent(pet_agent)

    # Example 1: Show diary entries
    console.print("\n[bold cyan]Example 1: Showing pet diary entries[/bold cyan]")
    result = await flock.run_async(
        start_agent=pet_agent,
        input={"user_request": "What has my pet been up to recently?"},
    )
    console.print(f"[bold]Agent Response:[/bold] {result.response}")

    # Example 2: Add a custom diary note
    console.print("\n[bold cyan]Example 2: Adding a custom diary note[/bold cyan]")
    result = await flock.run_async(
        start_agent=pet_agent,
        input={"user_request": "Add a note that Pixel caught a virtual mouse today!"},
    )
    console.print(f"[bold]Agent Response:[/bold] {result.response}")

    # Example 3: Show updated diary
    console.print("\n[bold cyan]Example 3: Showing updated diary[/bold cyan]")
    result = await flock.run_async(
        start_agent=pet_agent,
        input={"user_request": "Show me Pixel's diary entries"},
    )
    console.print(f"[bold]Agent Response:[/bold] {result.response}")

    # Display the diary entries in a table
    diary_module = None
    for name, module in pet_agent.modules.items():
        if isinstance(module, PetDiaryModule):
            diary_module = module
            break

    if diary_module:
        entries = diary_module.get_recent_entries(10)

        if entries:
            table = Table(title=f"{diary_module.config.pet_name}'s Diary")
            table.add_column("Date", style="cyan")
            table.add_column("Event Type", style="magenta")
            table.add_column("Description", style="green")

            for entry in entries:
                date = datetime.fromisoformat(entry["timestamp"]).strftime(
                    "%Y-%m-%d %H:%M"
                )
                table.add_row(
                    date, entry["event_type"].capitalize(), entry["description"]
                )

            console.print("\n")
            console.print(table)
        else:
            console.print("\n[yellow]No diary entries found.[/yellow]")

    # Show how the module enhances the agent
    console.print(
        Panel.fit(
            "The Pet Diary Module demonstrates several key features of Flock modules:\n\n"
            "1. [bold]Persistent Storage[/bold]: Diary entries are saved to a file and loaded when needed\n"
            "2. [bold]Automatic Event Detection[/bold]: The module analyzes agent interactions to detect events\n"
            "3. [bold]Context Enhancement[/bold]: Recent diary entries are added to the agent's context\n"
            "4. [bold]Tool Integration[/bold]: The module provides tools for agents to access the diary\n"
            "5. [bold]Separation of Concerns[/bold]: Core agent logic is separate from the diary functionality",
            title="Module Benefits",
            border_style="green",
        )
    )


# --------------------------------
# Interactive Mode
# --------------------------------
async def interactive_mode():
    """Run an interactive session with the pet agent and diary module."""
    console.print(
        Panel.fit(
            "🐱 Interactive Pet Caretaker Mode 🐱\n\n"
            "You can now interact directly with your virtual pet!\n"
            "The Pet Diary Module will record significant events automatically.\n\n"
            "Type 'exit' or 'quit' to end the session.\n"
            "Type 'diary' to view recent diary entries.",
            border_style="cyan",
        )
    )

    # Create a Flock instance
    flock = Flock(name="virtual_pet_with_diary", model=MODEL, show_flock_banner=False)

    # Create the pet caretaker agent
    pet_agent = FlockFactory.create_default_agent(
        name="pet_caretaker",
        description=(
            "You are a helpful virtual pet caretaker assistant. "
            "You help users take care of their virtual pet by using the available tools. "
            "For the pet's attributes: hunger, happiness, and energy, the scale is 0-100 "
            "where 0 is the worst possible state (starving, very sad, completely exhausted) "
            "and 100 is the best possible state (completely full, very happy, fully energetic)."
        ),
        input="user_request: str | The user's request about their virtual pet",
        output="response: str | Your helpful response to the user's request",
        tools=[
            get_pet_diary,
            add_diary_note,
            get_pet_status,
            feed_pet,
            play_with_pet,
            teach_trick,
            buy_item,
            get_mood_history,
            perform_trick,
        ],
        temperature=0.7,
        include_thought_process=True,
    )

    # Add the Pet Diary Module to the agent
    pet_diary_config = PetDiaryModuleConfig(
        pet_name="Pixel", diary_file="pet_diary.json"
    )
    pet_agent.add_component(
        config_instance=pet_diary_config, component_name="pet_diary"
    )

    # Add the agent to the flock
    flock.add_agent(pet_agent)

    # Get the diary module for direct access
    diary_module = None
    for name, module in pet_agent.modules.items():
        if isinstance(module, PetDiaryModule):
            diary_module = module
            break

    # Interactive loop
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

            # Check for diary command
            if user_request.lower() == "diary":
                if diary_module:
                    entries = diary_module.get_recent_entries(10)

                    if entries:
                        table = Table(title=f"{diary_module.config.pet_name}'s Diary")
                        table.add_column("Date", style="cyan")
                        table.add_column("Event Type", style="magenta")
                        table.add_column("Description", style="green")

                        for entry in entries:
                            date = datetime.fromisoformat(entry["timestamp"]).strftime(
                                "%Y-%m-%d %H:%M"
                            )
                            table.add_row(
                                date,
                                entry["event_type"].capitalize(),
                                entry["description"],
                            )

                        console.print("\n")
                        console.print(table)
                    else:
                        console.print("\n[yellow]No diary entries found.[/yellow]")
                continue

            # Process the user request with the agent
            console.print("[bold]Processing your request...[/bold]")
            result = await flock.run_async(
                start_agent=pet_agent, input={"user_request": user_request}
            )

            # Display the agent's response
            console.print(f"[bold green]Agent Response:[/bold green] {result.response}")

        except KeyboardInterrupt:
            console.print("\n[bold]Session interrupted. Goodbye![/bold]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e!s}")
            console.print("Please try again.")


# --------------------------------
# Main Execution
# --------------------------------
if __name__ == "__main__":
    # Run the example
    asyncio.run(run_pet_diary_example())

    # Run interactive mode
    asyncio.run(interactive_mode())

# --- YOUR TURN! ---
# 1. Extend the diary module:
#    - Add a method to search for entries by keyword
#    - Create a tool that lets the agent search the diary
#    - Try asking questions about past events
#
# 2. Create milestone detection:
#    - Add logic to detect when the pet reaches milestones (e.g., learning 5 tricks)
#    - Have the module automatically add special entries for these events
#    - Create a tool to show all milestones achieved
#
# 3. Implement diary analytics:
#    - Add methods to analyze patterns in the diary (e.g., most common activities)
#    - Create visualizations of the pet's activities over time
#    - Have the agent suggest activities based on what the pet hasn't done recently
#
# 4. Connect with the pet state:
#    - Integrate the diary module with the pet state from the tools-in-action example
#    - Record changes in the pet's stats over time
#    - Create a "pet history" visualization showing how stats have changed
#
# 5. Create a personalized story:
#    - Add a method that generates a story based on recent diary entries
#    - Have the agent tell a bedtime story to the pet using its recent experiences
#    - Save these stories in a separate "storybook" file
