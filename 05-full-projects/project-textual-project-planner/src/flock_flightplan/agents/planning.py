from flock.core import Flock, FlockFactory, flock_type
from flock.routers.default.default_router import (
    DefaultRouter,
    DefaultRouterConfig,
)
from pydantic import BaseModel, Field


@flock_type
class SchemaRoot(BaseModel):
    """Model representing the root element of the schema which defines the top-level components of the project."""

    allowed_children: dict[str, str] = Field(
        default={},
        description="Mapping of child types to cardinality ('single' or 'multiple')",
    )


@flock_type
class SchemaElement(BaseModel):
    """Model representing a structure schema element in the planning system.

    This model encapsulates the properties of schema elements defined in structure.yaml,
    providing a cleaner interface for working with node types.

    Attributes:
        node_type (str): The internal type identifier for this element
        display_name (str): Human-readable name for display purposes
        icon (str): Icon text representation used in the tree view
        allowed_children (Dict[str, str]): Mapping of child types to cardinality ('single' or 'multiple')
    """

    node_type: str = Field(description="The internal type identifier for this element")
    display_name: str = Field(description="Human-readable name for display purposes")
    emoji: str = Field(
        default="",
        description="Emoji text representation used in the tree view",
    )
    allowed_children: dict[str, str] = Field(
        default={},
        description="Mapping of child types to cardinality ('single' or 'multiple')",
    )


DESCRIPTION = """
Creates a planning structure for a project.

Example planning structure:

```yaml
root:
  allowed_children:
    ProjectPlan: multiple


ProjectPlan:
  display_name: "Project Plan" # Optional nicer name for display
  icon: " P " # Optional icon
  allowed_children:
    UserStory: multiple


UserStory:
  display_name: "User Story"
  icon: " U "
  allowed_children:
    Task: multiple

Task:
  display_name: "Task"
  icon: " T "
  allowed_children: {} # Tasks are leaf nodes here

```

"""


async def generate_planning_structure(user_input: str):
    flock = Flock(model="gpt-4.1-2025-04-14")

    project_type_agent = FlockFactory.create_default_agent(
        name="project_type_agent",
        description="A helpful assistant that determines the type of project based on the user's input.",
        input="user_input",
        output="project_type: str | high levelproject type like 'web development' - 'book writing' - 'data analysis'... and so on",
        write_to_file=True,
        no_output=True,
    )

    planning_schema_agent = FlockFactory.create_default_agent(
        name="planning_schema_agent",
        description=DESCRIPTION,
        input="project_type",
        output="root_element: SchemaRoot, implementation_plan: list[SchemaElement] | The schema structure of a plan to implement the project type. Think of the seperate steps needed to implement the user request. It should be a general plan for the type of project.",
        write_to_file=True,
        no_output=True,
    )

    template_agent = FlockFactory.create_default_agent(
        name="template_agent",
        description="An agent that generates content templates",
        input="root_element: SchemaRoot, implementation_plan: list[SchemaElement]",
        output="markdown_templates: list[tuple[str, str]] | Templates for the implementation of a project element. One template per project element. The template defines which information is needed to implement the project element. For example a template for a user story could contain the fields title - description - acceptance criteria - story points etc. The tuple contains the project element name and the template.",
        write_to_file=True,
        no_output=True,
    )

    flock.add_agent(project_type_agent)
    flock.add_agent(planning_schema_agent)
    flock.add_agent(template_agent)

    project_type_agent.handoff_router = DefaultRouter(
        name="project_type_router",
        config=DefaultRouterConfig(hand_off="planning_schema_agent"),
    )

    planning_schema_agent.handoff_router = DefaultRouter(
        name="planning_schema_router",
        config=DefaultRouterConfig(hand_off="template_agent"),
    )

    # template_agent.handoff_router = IterativeListGeneratorRouter(
    #     name="template_router",
    #     config=IterativeListGeneratorRouterConfig(
    #         target_list_field="markdown_templates",
    #         item_output_field="markdown_template : str | Template for the design of a document of the type of the project element",
    #         context_input_field="already_generated_templates",
    #     ),
    # )

    result = await flock.run_async(
        agent="project_type_agent",
        input={"user_input": user_input},
    )

    return result
