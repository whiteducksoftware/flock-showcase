# --------------------------------
# Pet State File Management
# --------------------------------
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from flock.core.flock_registry import flock_tool
from rich.console import Console
from rich.table import Table

PET_STATE_FILE = Path("pet_state.json")
console = Console()


def load_pet_state() -> Dict:
    """Load pet state from JSON file or create default if it doesn't exist."""
    if PET_STATE_FILE.exists():
        try:
            with open(PET_STATE_FILE, "r") as f:
                pet_data = json.load(f)

                # Convert datetime strings back to datetime objects
                pet_data["last_fed"] = datetime.fromisoformat(pet_data["last_fed"])
                pet_data["last_played"] = datetime.fromisoformat(
                    pet_data["last_played"]
                )

                return pet_data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            console.print(
                f"[red]Error loading pet state: {e}. Using default state.[/red]"
            )
            return create_default_pet_state()
    else:
        return create_default_pet_state()


def save_pet_state(pet_data: Dict) -> None:
    """Save pet state to JSON file."""
    # Convert datetime objects to ISO format strings for JSON serialization
    serializable_pet = pet_data.copy()
    serializable_pet["last_fed"] = pet_data["last_fed"].isoformat()
    serializable_pet["last_played"] = pet_data["last_played"].isoformat()

    with open(PET_STATE_FILE, "w") as f:
        json.dump(serializable_pet, f, indent=2)


def create_default_pet_state() -> Dict:
    """Create default pet state."""
    default_pet = {
        "name": "Pixel",
        "type": "digital cat",
        "hunger": 50,  # 0-100 (0: starving/worst, 100: full/best)
        "happiness": 50,  # 0-100 (0: sad/worst, 100: very happy/best)
        "energy": 50,  # 0-100 (0: exhausted/worst, 100: energetic/best)
        "last_fed": datetime.now() - timedelta(hours=5),
        "last_played": datetime.now() - timedelta(hours=3),
        "inventory": ["basic kibble", "toy mouse", "ball of yarn"],
        "tricks_known": ["sit", "paw"],
        "mood_history": [],  # Track mood changes over time
    }
    save_pet_state(default_pet)
    return default_pet


# Initialize pet state
PET = load_pet_state()

# --------------------------------
# Custom Tools
# --------------------------------


@flock_tool
def get_pet_status() -> Dict:
    """
    Get the current status of your virtual pet.
    Returns all pet attributes including hunger, happiness, and energy levels.
    """
    global PET
    # Load the latest state
    PET = load_pet_state()

    # Calculate time-based changes (pet gets hungry and less happy over time)
    hours_since_fed = (datetime.now() - PET["last_fed"]).total_seconds() / 3600
    hours_since_played = (datetime.now() - PET["last_played"]).total_seconds() / 3600

    # Decrease hunger by 5 points per hour since last fed (min 0)
    PET["hunger"] = max(0, PET["hunger"] - int(hours_since_fed * 5))

    # Decrease happiness by 3 points per hour since last played (min 0)
    PET["happiness"] = max(0, PET["happiness"] - int(hours_since_played * 3))

    # Energy recovers slowly over time (max 100)
    PET["energy"] = min(100, PET["energy"] + 2)

    # Update the mood history
    current_mood = calculate_mood(PET["hunger"], PET["happiness"], PET["energy"])
    if not PET["mood_history"] or PET["mood_history"][-1] != current_mood:
        PET["mood_history"].append(current_mood)
        if len(PET["mood_history"]) > 5:
            PET["mood_history"] = PET["mood_history"][-5:]

    # Save the updated state
    save_pet_state(PET)
    return PET


@flock_tool
def feed_pet(food_item: str) -> str:
    """
    Feed your pet with a specific food item.

    Args:
        food_item: The name of the food to feed your pet

    Returns:
        A description of how your pet responded to the food
    """
    global PET
    # Load the latest state
    PET = load_pet_state()

    # Check if the food is in inventory
    if food_item not in PET["inventory"]:
        return f"{PET['name']} looks confused. You don't have {food_item} in your inventory."

    # Different foods have different effects
    food_effects = {
        "basic kibble": {"hunger": 15, "happiness": 5, "energy": 3},
        "premium kibble": {"hunger": 25, "happiness": 10, "energy": 5},
        "gourmet fish": {"hunger": 40, "happiness": 20, "energy": 10},
        "treat": {"hunger": 5, "happiness": 15, "energy": 2},
    }

    # Default effect for unknown foods
    effect = food_effects.get(food_item, {"hunger": 10, "happiness": 5, "energy": 2})

    # Apply the effects
    PET["hunger"] = min(100, PET["hunger"] + effect["hunger"])
    PET["happiness"] = min(100, PET["happiness"] + effect["happiness"])
    PET["energy"] = min(100, PET["energy"] + effect["energy"])
    PET["last_fed"] = datetime.now()

    # If it's a consumable item, remove from inventory
    if food_item != "basic kibble":  # basic kibble is unlimited
        PET["inventory"].remove(food_item)

    responses = [
        f"{PET['name']} eats the {food_item} eagerly!",
        f"{PET['name']} nibbles on the {food_item} and purrs contentedly.",
        f"{PET['name']} devours the {food_item} in seconds!",
    ]

    # Save the updated state
    save_pet_state(PET)
    return random.choice(responses)


@flock_tool
def play_with_pet(activity: str) -> str:
    """
    Play with your pet using a specific activity or toy.

    Args:
        activity: The name of the activity or toy to use

    Returns:
        A description of how your pet responded to the play session
    """
    global PET
    # Load the latest state
    PET = load_pet_state()

    # Check if the toy is in inventory
    toy_activities = ["toy mouse", "ball of yarn", "laser pointer", "feather wand"]
    if activity in toy_activities and activity not in PET["inventory"]:
        return f"{PET['name']} looks excited, but you don't have a {activity} in your inventory."

    # Different activities have different effects
    activity_effects = {
        "toy mouse": {"happiness": 20, "energy": -10},
        "ball of yarn": {"happiness": 15, "energy": -5},
        "laser pointer": {"happiness": 25, "energy": -15},
        "feather wand": {"happiness": 20, "energy": -10},
        "petting": {"happiness": 10, "energy": 0},
        "chase": {"happiness": 30, "energy": -20},
    }

    # Default effect for unknown activities
    effect = activity_effects.get(activity, {"happiness": 10, "energy": -5})

    # Check if pet has enough energy
    if PET["energy"] + effect["energy"] < 0:
        return f"{PET['name']} seems too tired to play with the {activity} right now."

    # Apply the effects
    PET["happiness"] = min(100, PET["happiness"] + effect["happiness"])
    PET["energy"] = max(0, PET["energy"] + effect["energy"])
    PET["last_played"] = datetime.now()

    responses = [
        f"{PET['name']} has a great time playing with the {activity}!",
        f"{PET['name']} jumps and pounces on the {activity} excitedly!",
        f"{PET['name']} enjoys the {activity} and looks happier now.",
    ]

    # Save the updated state
    save_pet_state(PET)
    return random.choice(responses)


@flock_tool
def teach_trick(trick_name: str) -> str:
    """
    Try to teach your pet a new trick.

    Args:
        trick_name: The name of the trick to teach

    Returns:
        A description of your pet's learning progress
    """
    global PET
    # Load the latest state
    PET = load_pet_state()

    # Check if pet already knows this trick
    if trick_name in PET["tricks_known"]:
        return f"{PET['name']} already knows how to {trick_name}!"

    # Check if pet is in the right mood to learn
    if PET["hunger"] < 30:
        return f"{PET['name']} is too hungry to focus on learning right now."

    if PET["happiness"] < 40:
        return f"{PET['name']} doesn't seem interested in learning when unhappy."

    if PET["energy"] < 20:
        return f"{PET['name']} is too tired to learn new tricks right now."

    # Teaching consumes energy and increases happiness
    PET["energy"] = max(0, PET["energy"] - 15)
    PET["happiness"] = min(100, PET["happiness"] + 10)

    # 70% chance of success if all conditions are met
    if random.random() < 0.7:
        PET["tricks_known"].append(trick_name)
        save_pet_state(PET)
        return f"Success! {PET['name']} has learned how to {trick_name}!"
    else:
        save_pet_state(PET)
        return f"{PET['name']} tried to learn {trick_name}, but needs more practice."


@flock_tool
def buy_item(item_name: str, cost: int = 10) -> str:
    """
    Buy a new item for your pet.

    Args:
        item_name: The name of the item to buy
        cost: The cost of the item (default: 10)

    Returns:
        A confirmation message about the purchase
    """
    global PET
    # Load the latest state
    PET = load_pet_state()

    # In a real app, you'd check the user's balance
    # For this example, we'll just add the item to inventory

    if item_name in PET["inventory"]:
        return f"You already have {item_name} in your inventory."

    PET["inventory"].append(item_name)
    save_pet_state(PET)
    return f"You purchased {item_name} for {cost} coins! It's been added to your inventory."


@flock_tool
def get_mood_history() -> List[str]:
    """
    Get the history of your pet's mood changes.

    Returns:
        A list of mood states from oldest to newest
    """
    global PET
    # Load the latest state
    PET = load_pet_state()
    return PET["mood_history"]


@flock_tool
def perform_trick(trick_name: str) -> str:
    """
    Ask your pet to perform a trick it knows.

    Args:
        trick_name: The name of the trick to perform

    Returns:
        A description of your pet's performance
    """
    global PET
    # Load the latest state
    PET = load_pet_state()

    if trick_name not in PET["tricks_known"]:
        return f"{PET['name']} doesn't know how to {trick_name} yet."

    if PET["energy"] < 10:
        return f"{PET['name']} is too tired to perform tricks right now."

    # Performing tricks uses a small amount of energy
    PET["energy"] = max(0, PET["energy"] - 5)
    PET["happiness"] = min(100, PET["happiness"] + 5)

    trick_responses = {
        "sit": [
            f"{PET['name']} sits down perfectly!",
            f"{PET['name']} sits and looks up at you expectantly.",
        ],
        "paw": [
            f"{PET['name']} extends a paw gracefully.",
            f"{PET['name']} reaches out with a paw and taps your hand.",
        ],
        "roll": [
            f"{PET['name']} rolls over in a complete circle!",
            f"{PET['name']} flops onto their back and rolls around playfully.",
        ],
        "speak": [
            f"{PET['name']} makes an adorable sound!",
            f"{PET['name']} meows loudly on command.",
        ],
        "jump": [
            f"{PET['name']} leaps into the air with surprising height!",
            f"{PET['name']} jumps up and does a little spin.",
        ],
    }

    responses = trick_responses.get(
        trick_name, [f"{PET['name']} performs the {trick_name} trick perfectly!"]
    )

    save_pet_state(PET)
    return random.choice(responses)


# --------------------------------
# Helper Functions
# --------------------------------


def calculate_mood(hunger: int, happiness: int, energy: int) -> str:
    """Calculate the pet's current mood based on its stats."""
    if hunger < 20:
        return "hungry"
    elif happiness < 30:
        return "sad"
    elif energy < 20:
        return "tired"
    elif happiness > 80 and hunger > 70:
        return "ecstatic"
    elif happiness > 60:
        return "happy"
    else:
        return "content"


def display_pet_status(pet_data: Dict):
    """Display the pet's status in a nice formatted way."""
    status_table = Table(title=f"{pet_data['name']} the {pet_data['type']}")

    # Add columns
    status_table.add_column("Attribute", style="cyan")
    status_table.add_column("Value", style="green")

    # Add rows for basic stats
    status_table.add_row("Hunger", f"{pet_data['hunger']}/100")
    status_table.add_row("Happiness", f"{pet_data['happiness']}/100")
    status_table.add_row("Energy", f"{pet_data['energy']}/100")

    # Calculate and add current mood
    mood = calculate_mood(pet_data["hunger"], pet_data["happiness"], pet_data["energy"])
    status_table.add_row("Current Mood", mood.capitalize())

    # Add time info
    status_table.add_row("Last Fed", pet_data["last_fed"].strftime("%H:%M:%S"))
    status_table.add_row("Last Played", pet_data["last_played"].strftime("%H:%M:%S"))

    # Add inventory and tricks
    status_table.add_row("Inventory", ", ".join(pet_data["inventory"]))
    status_table.add_row("Tricks Known", ", ".join(pet_data["tricks_known"]))

    console.print(status_table)
