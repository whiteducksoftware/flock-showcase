"""
Defining Complex Pydantic Types in Flock

Purpose: Demonstrate how to create and use complex nested Pydantic models with Flock.

Use Case: Space Exploration Game 🚀 - Generate detailed space missions with nested structures.

Highlights:
- Define multiple nested Pydantic models with complex relationships
- Use Field validation constraints to set up possible values
- Demonstrate enum types, lists of models, and dictionaries
- Show how Flock handles complex nested structures
"""

import enum
import os
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from flock.core import Flock, FlockFactory
from flock.core.flock_registry import flock_type
from pydantic import BaseModel, Field, field_validator, model_validator
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# --- Configuration ---
console = Console()
MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4o")
console.print(f"[grey50]Using model: {MODEL}[/grey50]")


# --------------------------------
# Define the Pydantic data models
# --------------------------------


# Enum for planet types
class PlanetType(str, enum.Enum):
    TERRESTRIAL = "terrestrial"
    GAS_GIANT = "gas_giant"
    ICE_GIANT = "ice_giant"
    DWARF = "dwarf"
    SUPER_EARTH = "super_earth"
    HOT_JUPITER = "hot_jupiter"


# Enum for resource rarity
class ResourceRarity(str, enum.Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EXOTIC = "exotic"
    LEGENDARY = "legendary"


@flock_type
class Coordinates(BaseModel):
    """3D coordinates in space."""

    x: float = Field(
        ...,
        description="X coordinate in light years from Sol (between -1000 and 1000)",
        ge=-1000,
        le=1000,
    )
    y: float = Field(
        ...,
        description="Y coordinate in light years from Sol (between -1000 and 1000)",
        ge=-1000,
        le=1000,
    )
    z: float = Field(
        ...,
        description="Z coordinate in light years from Sol (between -1000 and 1000)",
        ge=-1000,
        le=1000,
    )

    def distance_from_sol(self) -> float:
        """Calculate distance from Sol (0,0,0)."""
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5


@flock_type
class Resource(BaseModel):
    """A resource that can be harvested from a celestial body."""

    name: str = Field(
        ...,
        description="Name of the resource (must be capitalized)",
        pattern=r"^[A-Z].*",
    )
    rarity: ResourceRarity = Field(
        ..., description="Rarity classification of the resource"
    )
    value_per_unit: int = Field(
        ...,
        description="Value per unit in credits. High-value resources (>1000) should have hazard level of at least 3",
        gt=0,
    )
    hazard_level: int = Field(
        ...,
        description="Hazard level from 0-10. High hazard resources (>8) should have value of at least 500 credits",
        ge=0,
        le=10,
    )

    @field_validator("name")
    @classmethod
    def name_must_be_scientific(cls, v: str) -> str:
        """Ensure resource names follow scientific naming convention."""
        if not v[0].isupper():
            raise ValueError("Resource names must be capitalized")
        return v

    @model_validator(mode="after")
    def check_value_hazard_correlation(self) -> "Resource":
        """Ensure high-value resources tend to be more hazardous."""
        value = self.value_per_unit
        hazard = self.hazard_level

        # Very valuable resources should have some hazard
        if value > 1000 and hazard < 3:
            raise ValueError(
                "High-value resources must have a hazard level of at least 3"
            )

        # Very hazardous resources should have some value
        if hazard > 8 and value < 500:
            raise ValueError(
                "Highly hazardous resources must have a value of at least 500 credits"
            )

        return self


@flock_type
class Atmosphere(BaseModel):
    """Atmospheric composition and conditions."""

    breathable: bool = Field(
        ..., description="Whether the atmosphere is breathable by humans"
    )
    composition: Dict[str, float] = Field(
        ...,
        description="Chemical composition as element:percentage. Percentages should sum to approximately 100%",
    )
    pressure: float = Field(
        ..., description="Atmospheric pressure in Earth atmospheres", ge=0
    )
    temperature_range: tuple[float, float] = Field(
        ...,
        description="Temperature range in Celsius. Minimum temperature must be less than maximum temperature",
    )

    @field_validator("composition")
    @classmethod
    def composition_must_sum_to_100(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Ensure composition percentages sum to approximately 100%."""
        total = sum(v.values())
        if not 99.5 <= total <= 100.5:
            raise ValueError(
                f"Composition percentages must sum to approximately 100% (got {total}%)"
            )
        return v

    @field_validator("temperature_range")
    @classmethod
    def validate_temperature_range(cls, v: tuple[float, float]) -> tuple[float, float]:
        """Ensure min temperature is less than max temperature."""
        if v[0] >= v[1]:
            raise ValueError(
                f"Minimum temperature ({v[0]}) must be less than maximum temperature ({v[1]})"
            )
        return v


@flock_type
class CelestialBody(BaseModel):
    """Base class for all celestial bodies."""

    name: str = Field(
        ...,
        description="Name of the celestial body (must be capitalized)",
        pattern=r"^[A-Z].*",
    )
    mass: float = Field(..., description="Mass in Earth masses", gt=0)
    radius: float = Field(..., description="Radius in Earth radii", gt=0)
    coordinates: Coordinates = Field(..., description="Location in space")
    resources: List[Resource] = Field(
        default_factory=list, description="Available resources"
    )

    @field_validator("name")
    @classmethod
    def name_must_be_proper(cls, v: str) -> str:
        """Ensure celestial body names are properly capitalized."""
        if not v[0].isupper():
            raise ValueError("Celestial body names must be capitalized")
        return v


@flock_type
class Planet(CelestialBody):
    """A planet that can be explored."""

    type: PlanetType = Field(..., description="Type of planet")
    habitable_zone: bool = Field(
        ...,
        description="Whether the planet is in the habitable zone. Note: Gas giants and ice giants cannot be in habitable zone",
    )
    atmosphere: Optional[Atmosphere] = Field(
        None,
        description="Atmospheric conditions if present. Note: Gas giants and ice giants must have an atmosphere",
    )
    moons: int = Field(0, description="Number of moons", ge=0)
    rings: bool = Field(False, description="Whether the planet has rings")
    colonized: bool = Field(False, description="Whether the planet has been colonized")

    @model_validator(mode="after")
    def validate_planet_properties(self) -> "Planet":
        """Validate planet properties based on type."""
        planet_type = self.type
        atmosphere = self.atmosphere

        # Gas giants and ice giants must have an atmosphere
        if (
            planet_type in [PlanetType.GAS_GIANT, PlanetType.ICE_GIANT]
            and atmosphere is None
        ):
            raise ValueError(f"{planet_type} planets must have an atmosphere")

        # Gas giants and ice giants cannot be habitable
        if (
            planet_type
            in [
                PlanetType.GAS_GIANT,
                PlanetType.ICE_GIANT,
            ]
            and self.habitable_zone
        ):
            raise ValueError(f"{planet_type} planets cannot be in the habitable zone")

        return self


@flock_type
class CrewMember(BaseModel):
    """A crew member for a space mission."""

    name: str = Field(
        ...,
        description="Full name of the crew member (must include first and last name)",
        pattern=r"^[A-Za-z]+ [A-Za-z]+",
    )
    specialization: Literal[
        "pilot", "engineer", "scientist", "doctor", "security", "diplomat"
    ] = Field(..., description="Primary role")
    experience_years: int = Field(..., description="Years of experience", ge=0)
    special_skills: List[str] = Field(
        default_factory=list, description="Special skills and abilities"
    )

    @field_validator("name")
    @classmethod
    def name_must_have_space(cls, v: str) -> str:
        """Ensure name has at least first and last name."""
        if " " not in v:
            raise ValueError("Name must include both first and last name")
        return v


@flock_type
class Spacecraft(BaseModel):
    """A spacecraft for interplanetary missions."""

    name: str = Field(
        ...,
        description="Name of the spacecraft (must be capitalized)",
        pattern=r"^[A-Z].*",
    )
    class_type: str = Field(..., description="Class/model of the spacecraft")
    max_crew: int = Field(..., description="Maximum crew capacity", gt=0)
    range_light_years: float = Field(
        ..., description="Maximum range in light years", gt=0
    )
    fuel_capacity: float = Field(..., description="Fuel capacity in tons", gt=0)
    cargo_capacity: float = Field(..., description="Cargo capacity in tons", ge=0)
    special_equipment: List[str] = Field(
        default_factory=list, description="Special equipment installed"
    )

    @field_validator("name")
    @classmethod
    def validate_spacecraft_name(cls, v: str) -> str:
        """Ensure spacecraft name is properly formatted."""
        if not v[0].isupper():
            raise ValueError("Spacecraft names must be capitalized")
        return v


@flock_type
class MissionObjective(BaseModel):
    """An objective for a space mission."""

    title: str = Field(..., description="Title of the objective")
    description: str = Field(..., description="Detailed description")
    priority: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Priority level. Critical priority missions must have rewards of at least 10,000 credits",
    )
    estimated_duration_days: float = Field(
        ..., description="Estimated time to complete in days", gt=0
    )
    reward_credits: int = Field(
        ...,
        description="Reward for completion in credits. Critical missions require at least 10,000 credits",
        ge=0,
    )

    @model_validator(mode="after")
    def validate_priority_reward(self) -> "MissionObjective":
        """Ensure critical missions have appropriate rewards."""
        if self.priority == "critical" and self.reward_credits < 10000:
            raise ValueError(
                "Critical missions must have rewards of at least 10,000 credits"
            )
        return self


@flock_type
class SpaceMission(BaseModel):
    """A complete space exploration mission."""

    mission_id: str = Field(..., description="Unique mission identifier")
    title: str = Field(..., description="Mission title")
    spacecraft: Spacecraft = Field(
        ..., description="Spacecraft assigned to the mission"
    )
    crew: List[CrewMember] = Field(
        ...,
        description="Crew members assigned to the mission. Must not exceed spacecraft capacity. Must include at least one pilot and one engineer",
    )
    destination: Planet = Field(..., description="Primary destination")
    secondary_destinations: List[CelestialBody] = Field(
        default_factory=list, description="Secondary destinations"
    )
    objectives: List[MissionObjective] = Field(..., description="Mission objectives")
    launch_date: datetime = Field(..., description="Planned launch date")
    estimated_return_date: datetime = Field(
        ..., description="Estimated return date. Must be after launch date"
    )
    mission_brief: str = Field(..., description="Brief mission summary")
    risk_assessment: str = Field(..., description="Risk assessment summary")

    @field_validator("crew")
    @classmethod
    def validate_crew_size(cls, v: List[CrewMember], info: Any) -> List[CrewMember]:
        """Ensure crew size doesn't exceed spacecraft capacity."""
        if info.data.get("spacecraft") and len(v) > info.data["spacecraft"].max_crew:
            raise ValueError(
                f"Crew size ({len(v)}) exceeds spacecraft capacity ({info.data['spacecraft'].max_crew})"
            )
        return v

    @field_validator("estimated_return_date")
    @classmethod
    def return_after_launch(cls, v: datetime, info: Any) -> datetime:
        """Ensure return date is after launch date."""
        if info.data.get("launch_date") and v <= info.data["launch_date"]:
            raise ValueError("Estimated return date must be after launch date")
        return v

    @model_validator(mode="after")
    def validate_mission_requirements(self) -> "SpaceMission":
        """Ensure mission has necessary specialists."""
        specializations = [member.specialization for member in self.crew]

        # Every mission needs a pilot
        if "pilot" not in specializations:
            raise ValueError("Mission requires at least one pilot")

        # Every mission needs an engineer
        if "engineer" not in specializations:
            raise ValueError("Mission requires at least one engineer")

        return self


# --------------------------------
# Create a new Flock instance
# --------------------------------
flock = Flock(name="space_mission_generator", model=MODEL, show_flock_banner=False)

# --------------------------------
# Define the Agent using the Pydantic type
# --------------------------------
mission_agent = FlockFactory.create_default_agent(
    name="mission_agent",
    description="Generates detailed space exploration mission profiles.",
    input="mission_parameters: dict | Parameters for mission generation including mission type and risk level and crew size.",
    output="mission: SpaceMission | A complete space mission profile with all required details.",
    temperature=0.7,
)
flock.add_agent(mission_agent)


# --------------------------------
# Run the Flock
# --------------------------------
def run_example():
    console.print(
        Panel.fit(
            "[bold cyan]Space Exploration Mission Generator[/bold cyan]",
            subtitle="Complex Pydantic Models Example",
        )
    )

    # Example mission parameters
    mission_params = {
        "mission_type": "exploration",
        "risk_level": "medium",
        "crew_size": 4,
        "mission_duration_days": 120,
        "special_requirements": ["resource survey", "first contact protocol"],
    }

    console.print("[yellow]Generating space mission profile...[/yellow]")

    try:
        result = flock.run(
            start_agent="mission_agent",
            input={"mission_parameters": mission_params},
        )

        # Display the mission details
        if hasattr(result, "mission") and isinstance(result.mission, SpaceMission):
            mission = result.mission

            # Create a rich table for mission details
            mission_table = Table(
                title=f"Mission: {mission.title} ({mission.mission_id})"
            )
            mission_table.add_column("Property", style="cyan")
            mission_table.add_column("Value", style="green")

            mission_table.add_row(
                "Spacecraft",
                f"{mission.spacecraft.name} ({mission.spacecraft.class_type})",
            )
            mission_table.add_row(
                "Destination",
                f"{mission.destination.name} ({mission.destination.type.value})",
            )
            mission_table.add_row(
                "Launch Date", mission.launch_date.strftime("%Y-%m-%d")
            )
            mission_table.add_row(
                "Return Date", mission.estimated_return_date.strftime("%Y-%m-%d")
            )
            mission_table.add_row("Mission Brief", mission.mission_brief)
            mission_table.add_row("Risk Assessment", mission.risk_assessment)

            console.print(mission_table)

            # Display crew details
            crew_table = Table(title="Crew Manifest")
            crew_table.add_column("Name", style="cyan")
            crew_table.add_column("Role", style="green")
            crew_table.add_column("Experience", style="yellow")
            crew_table.add_column("Special Skills", style="magenta")

            for crew_member in mission.crew:
                crew_table.add_row(
                    crew_member.name,
                    crew_member.specialization,
                    f"{crew_member.experience_years} years",
                    ", ".join(crew_member.special_skills)
                    if crew_member.special_skills
                    else "None",
                )

            console.print(crew_table)

            # Display mission objectives
            objectives_table = Table(title="Mission Objectives")
            objectives_table.add_column("Title", style="cyan")
            objectives_table.add_column("Priority", style="green")
            objectives_table.add_column("Duration", style="yellow")
            objectives_table.add_column("Reward", style="magenta")

            for objective in mission.objectives:
                objectives_table.add_row(
                    objective.title,
                    objective.priority,
                    f"{objective.estimated_duration_days} days",
                    f"{objective.reward_credits:,} credits",
                )

            console.print(objectives_table)

            # Display destination details
            dest = mission.destination
            console.print(
                Panel.fit(
                    f"[bold]Primary Destination: {dest.name}[/bold]\n"
                    f"Type: {dest.type.value}\n"
                    f"Mass: {dest.mass} Earth masses\n"
                    f"Radius: {dest.radius} Earth radii\n"
                    f"Distance from Sol: {dest.coordinates.distance_from_sol():.2f} light years\n"
                    f"Habitable: {'Yes' if dest.habitable_zone else 'No'}\n"
                    f"Colonized: {'Yes' if dest.colonized else 'No'}\n"
                    f"Moons: {dest.moons}\n"
                    f"Rings: {'Yes' if dest.rings else 'No'}\n"
                    f"Resources: {', '.join(r.name for r in dest.resources) if dest.resources else 'None detected'}"
                )
            )

            # Display spacecraft details
            spacecraft = mission.spacecraft
            console.print(
                Panel.fit(
                    f"[bold]Spacecraft: {spacecraft.name}[/bold]\n"
                    f"Class: {spacecraft.class_type}\n"
                    f"Max Crew: {spacecraft.max_crew}\n"
                    f"Range: {spacecraft.range_light_years} light years\n"
                    f"Fuel Capacity: {spacecraft.fuel_capacity} tons\n"
                    f"Cargo Capacity: {spacecraft.cargo_capacity} tons\n"
                    f"Special Equipment: {', '.join(spacecraft.special_equipment) if spacecraft.special_equipment else 'None'}"
                )
            )

            console.print(f"[grey50](Object Type: {type(mission)})[/grey50]")

        else:
            console.print(
                "[bold red]Agent did not return the expected 'mission' field or it wasn't a SpaceMission object.[/bold red]"
            )
            console.print("[bold red]Raw result:[/bold red]")
            console.print(result)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        console.print(
            "[bold red]Please ensure your API key is set and the model is accessible.[/bold red]"
        )


# --------------------------------
# Run the example if this script is executed directly
# --------------------------------
if __name__ == "__main__":
    run_example()


# --- YOUR TURN! ---
# 1. Extend the `SpaceMission` model:
#    - Add a new nested model, e.g., `@flock_type class MissionLog(BaseModel): entry_date: datetime; author: str; content: str`
#    - Add a field to SpaceMission: `logs: List[MissionLog] = Field(default_factory=list)`
#
# 2. Add more complex constraints through Field descriptions:
#    - Add a description to crew field to ensure each specialization appears at most twice
#    - Add a description to estimated_return_date to ensure it matches expected mission duration
#
# 3. Create a new mission type:
#    - Define a new `@flock_type class RescueMission(SpaceMission)` that inherits from SpaceMission
#    - Add fields specific to rescue missions like `rescue_target: str` and `emergency_level: int`
#    - Add a description to ensure rescue missions have a doctor in the crew
#
# 4. Experiment with Union types:
#    - Create a `@flock_type class AsteroidBelt(CelestialBody)` with specific asteroid properties
#    - Change `secondary_destinations: List[CelestialBody]` to `secondary_destinations: List[Union[Planet, AsteroidBelt]]`
#    Does Flock handle generating the correct type based on context?
