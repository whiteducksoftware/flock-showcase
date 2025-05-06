# --------------------------------
# Pet Diary Tool for Agent Access
# --------------------------------
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from flock.core.flock_registry import flock_tool
from flock.core.logging.logging import get_logger

logger = get_logger("pet_diary")


@flock_tool
def get_pet_diary(entries: int = 5) -> List[Dict]:
    """
    Get recent entries from your pet's diary.

    Args:
        entries: Number of recent entries to retrieve (default: 5)

    Returns:
        List of diary entries with timestamp, event type, and description
    """
    # Read diary entries directly from file
    diary_path = Path("pet_diary.json")
    if not diary_path.exists():
        return [{"error": "Pet diary not found"}]

    try:
        with open(diary_path, "r") as f:
            all_entries = json.load(f)

        # Get the most recent entries
        recent_entries = all_entries[-entries:] if all_entries else []

        # Format the entries for better readability
        formatted_entries = []
        for entry in recent_entries:
            formatted_entries.append(
                {
                    "date": datetime.fromisoformat(entry["timestamp"]).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    "event_type": entry["event_type"],
                    "description": entry["description"],
                }
            )

        return formatted_entries
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Error reading diary: {e}")
        return [{"error": f"Error reading diary: {str(e)}"}]


@flock_tool
def add_diary_note(note: str, pet_name: str = "Pixel") -> str:
    """
    Add a custom note to your pet's diary.

    Args:
        note: The note to add to the diary
        pet_name: The name of your pet (default: Pixel)

    Returns:
        Confirmation message
    """
    diary_path = Path("pet_diary.json")

    # Load existing entries or create new diary
    if diary_path.exists():
        try:
            with open(diary_path, "r") as f:
                diary_entries = json.load(f)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error loading diary: {e}. Creating new diary.")
            diary_entries = []
    else:
        diary_entries = []

    # Create new entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "note",
        "description": note,
        "details": {"custom": True},
    }

    # Add entry to diary
    diary_entries.append(entry)

    # Limit the number of entries (keep most recent 100)
    if len(diary_entries) > 100:
        diary_entries = diary_entries[-100:]

    # Save updated diary
    with open(diary_path, "w") as f:
        json.dump(diary_entries, f, indent=2)

    return f"Added note to {pet_name}'s diary: {note}"
