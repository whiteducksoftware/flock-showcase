from typing import Any, Literal, Optional
from flock.core.flock_registry import flock_type
from pydantic import BaseModel, Field
from rich.table import Table
from rich import box
from pathlib import Path
from textual.widgets import RichLog
from rich.markdown import Markdown
log : RichLog = None

def set_app_log(log_component):
    """Set the app's RichLog component for output"""
    global log
    log = log_component

@flock_type
class OutputData(BaseModel):
    name: str = Field(..., description="Name of the output")
    description: str = Field(
        ...,
        description="High level description of the data and functionality of the app, as well as design decisions. In beautiful markdown.",
    )
    output_dictionary_definition: str = Field(
        ..., description="Explanation of the output dictionary and the data it contains"
    )
    output: dict[str, Any] = Field(
        ...,
        description="The output dictionary. Usually a dictionary with keys equals paths to files, and values equal the content of the files.",
    )

    # beautiful rendering of the output
    def render_summary(self):
        log.write("\n")
        log.write(f"[bold blue]{self.name}")
        log.write("\n")
        log.write(self.description)
        log.write("\n")
        log.write(self.output_dictionary_definition)

    def render_output_files(self, output_prefix: str = ".project/"):
        """
        Renders the output files in a beautiful table format.

        Args:
            console: The Rich console instance to use for output
            output_prefix: Optional prefix to prepend to file paths (defaults to '.project/')
        """
        log.write("\n")
        log.write("[bold cyan]Output Files")
        log.write("\n")

        # Create a nice table to display the files
        files_table = Table(title="Generated Files", box=box.ROUNDED)
        files_table.add_column("File Path", style="cyan")
        files_table.add_column("Status", style="green")
        files_table.add_column("Size", style="magenta")

        file_count = 0

        # Process each output file
        for file_path, content in self.output.items():
            file_path_with_prefix = f"{output_prefix}{file_path}"
            # if is directory create and skip
            if Path(file_path_with_prefix).is_dir():
                Path(file_path_with_prefix).mkdir(parents=True, exist_ok=True)
                continue

            file_count += 1

            # Calculate the content size
            content_size = len(content) if content else 0
            size_display = (
                f"{content_size / 1024:.2f} KB"
                if content_size > 1024
                else f"{content_size} bytes"
            )

            # Create entry in the table
            try:
                # Create the directory if it doesn't exist
                Path(file_path_with_prefix).parent.mkdir(parents=True, exist_ok=True)

                # Write the file content
                with open(file_path_with_prefix, "w", encoding="utf-8") as f:
                    f.write(content)

                files_table.add_row(
                    file_path_with_prefix, "[green]✓ Created[/green]", size_display
                )
            except Exception as e:
                files_table.add_row(
                    file_path_with_prefix, f"[red]✗ Error: {str(e)}[/red]", size_display
                )

        if file_count > 0:
            log.write(files_table)
            log.write(
                f"\n[green]Successfully generated {file_count} files.[/green]\n"
            )
        else:
            log.write("[yellow]No output files were generated.[/yellow]\n")

        log.write("[bold cyan]End of Output")

class ProjectFile(BaseModel):
    file_id: str = Field(..., description="Unique identifier for the file")
    description: str = Field(..., description="Description of the file")
    file_path: str = Field(..., description="Path to the file")
    content: str = Field(..., description="Content of the file")
    line_count: int = Field(..., description="Number of lines in the file")

class ProjectCodeFile(ProjectFile):
    dependencies: list[str] = Field(..., description="List of file ids that must be created before this one")
    used_by: list[str] = Field(..., description="List of file ids that depend on this one")
    complexity_metrics: dict[str, Any] = Field(default_factory=dict, description="Code quality and complexity metrics")


@flock_type
class Repository(BaseModel):
    name: str = Field(..., description="Name of the repository")
    statistics: str = Field(..., description="Statistics of the repository")
    project_files: list[ProjectFile | ProjectCodeFile] = Field(..., description="Output data of the repository")

    def render_summary(self) -> None:
        """
        Render a summary of the repository in a beautiful format.
        
        Args:
            console: The Rich console instance to use for output
        """
        log.write("\n")
        log.write(f"[bold blue]{self.name}")
        log.write("\n")
        
        # Create a table for statistics
        stats_table = Table(title="Repository Statistics", box=box.ROUNDED)
        stats_table.add_column("Statistic", style="cyan")
        stats_table.add_column("Value", style="green")
        
        # Parse statistics string into individual items
        for stat_line in self.statistics.strip().split('\n'):
            if stat_line and '-' in stat_line:
                key, value = stat_line.split(':', 1) if ':' in stat_line else stat_line.split('-', 1)
                stats_table.add_row(key.strip('- '), value.strip())
        
        log.write(stats_table)
        log.write("\n")
    
    def render_files(self, max_files: int = 20) -> None:
        """
        Render the repository files in a beautiful table format.
        
        Args:
            console: The Rich console instance to use for output
            max_files: Maximum number of files to display (default: 20)
        """
        log.write("\n")
        log.write("[bold cyan]Repository Files")
        log.write("\n")
        
        # Create a table for files
        files_table = Table(title="Project Files", box=box.ROUNDED)
        files_table.add_column("File ID", style="cyan")
        files_table.add_column("Path", style="magenta")
        files_table.add_column("Lines", style="green")
        files_table.add_column("Type", style="yellow")
        files_table.add_column("Complexity", style="red")
        files_table.add_column("Maintainability", style="blue")
        
        # Add files to the table (limited to max_files)
        for file in self.project_files[:max_files]:
            file_type = "Code File" if isinstance(file, ProjectCodeFile) else "File"
            
            complexity = "-"
            maintainability = "-"
            if isinstance(file, ProjectCodeFile) and file.complexity_metrics:
                cc = file.complexity_metrics.get("cyclomatic_complexity", {})
                mi = file.complexity_metrics.get("maintainability_index", {})
                
                if cc and "rank" in cc:
                    complexity = f"{cc.get('total', '?')} ({cc.get('rank', '?')})"
                
                if mi and "rank" in mi:
                    maintainability = f"{int(mi.get('value', 0))} ({mi.get('rank', '?')})"
            
            files_table.add_row(
                file.file_id,
                file.file_path,
                str(file.line_count),
                file_type,
                complexity,
                maintainability
            )
        
        if len(self.project_files) > max_files:
            files_table.add_row(
                "...",
                f"[yellow]And {len(self.project_files) - max_files} more files...[/yellow]",
                "",
                "",
                "",
                ""
            )
        
        log.write(files_table)
        
        # Dependency information (only if there are ProjectCodeFiles)
        code_files = [f for f in self.project_files if isinstance(f, ProjectCodeFile)]
        if code_files:
            log.write("\n")
            log.write("[bold cyan]File Dependencies")
            log.write("\n")
            
            deps_table = Table(title="Dependencies Between Files", box=box.ROUNDED)
            deps_table.add_column("File", style="cyan")
            deps_table.add_column("Depends On", style="magenta")
            deps_table.add_column("Used By", style="green")
            
            for file in code_files[:max(10, max_files // 2)]:  # Show fewer files in dependency table
                # Get actual file paths instead of IDs for better readability
                depends_on_paths = []
                for dep_id in file.dependencies:
                    for f in self.project_files:
                        if f.file_id == dep_id:
                            depends_on_paths.append(f.file_path)
                            break
                
                used_by_paths = []
                for used_id in file.used_by:
                    for f in self.project_files:
                        if f.file_id == used_id:
                            used_by_paths.append(f.file_path)
                            break
                
                deps_table.add_row(
                    file.file_path,
                    "\n".join(depends_on_paths[:5]) + ("\n..." if len(depends_on_paths) > 5 else ""),
                    "\n".join(used_by_paths[:5]) + ("\n..." if len(used_by_paths) > 5 else "")
                )
            
            if len(code_files) > max(10, max_files // 2):
                deps_table.add_row(
                    "[yellow]And more files...[/yellow]",
                    "",
                    ""
                )
                
            log.write(deps_table)
            
            # New Code Metrics Table
            files_with_metrics = [f for f in code_files if isinstance(f, ProjectCodeFile) and f.complexity_metrics]
            if files_with_metrics:
                log.write("\n")
                log.write("[bold cyan]Code Quality Metrics")
                log.write("\n")
                
                metrics_table = Table(title="Code Complexity and Quality", box=box.ROUNDED)
                metrics_table.add_column("File", style="cyan")
                metrics_table.add_column("Cyclomatic Complexity", style="red")
                metrics_table.add_column("Maintainability", style="blue")
                metrics_table.add_column("Code Smells", style="yellow")
                
                for file in files_with_metrics[:max(10, max_files // 2)]:
                    metrics = file.complexity_metrics
                    cc = metrics.get("cyclomatic_complexity", {})
                    mi = metrics.get("maintainability_index", {})
                    smells = metrics.get("code_smells", [])
                    
                    cc_display = "[grey]-[/grey]"
                    if cc:
                        rank = cc.get("rank", "?")
                        rank_color = {
                            "A": "green", "B": "green",
                            "C": "yellow", "D": "red",
                            "F": "red bold"
                        }.get(rank, "white")
                        cc_display = f"Total: {cc.get('total', '?')} | Avg: {cc.get('average', '?')} | Rank: [{rank_color}]{rank}[/{rank_color}]"
                    
                    mi_display = "[grey]-[/grey]"
                    if mi:
                        rank = mi.get("rank", "?")
                        rank_color = {
                            "A": "green", "B": "green",
                            "C": "yellow", "D": "red",
                            "F": "red bold"
                        }.get(rank, "white")
                        mi_display = f"Index: {int(mi.get('value', 0))} | Rank: [{rank_color}]{rank}[/{rank_color}]"
                    
                    smells_display = "[grey]None detected[/grey]"
                    if smells:
                        smells_list = []
                        for i, smell in enumerate(smells[:3]):  # Show up to 3 smells
                            smells_list.append(f"{smell['type']} in {smell['location']}")
                        if len(smells) > 3:
                            smells_list.append(f"...and {len(smells) - 3} more")
                        smells_display = "\n".join(smells_list)
                    
                    metrics_table.add_row(
                        file.file_path,
                        cc_display,
                        mi_display,
                        smells_display
                    )
                
                if len(files_with_metrics) > max(10, max_files // 2):
                    metrics_table.add_row(
                        "[yellow]And more files...[/yellow]",
                        "",
                        "",
                        ""
                    )
                    
                log.write(metrics_table)
        
        log.write("[bold cyan]End of Repository")
    
    def save_to_json(self, output_path: str) -> bool:
        """
        Save the repository data to a JSON file.
        
        Args:
            output_path: The path where to save the JSON file
            console: Optional Rich console for output messages
            
        Returns:
            True if successful, False otherwise
        """
        import json
        from pathlib import Path
        
        try:
            # Convert repository to dict and save as JSON
            repo_dict = self.dict()
            file_path = Path(output_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(repo_dict, f, indent=2)
            
            log.write(f"\n[green]Repository data saved to {output_path}[/green]")
            
            return True
        except Exception as e:
            log.write(f"\n[red]Error saving repository data: {str(e)}[/red]")
            return False
            
    def save_to_markdown(self, output_path: str) -> bool:
        """
        Save the repository data to a Markdown file.
        This exports the same data as save_to_json but in Markdown format.
        
        Args:
            output_path: The path where to save the Markdown file
            console: Optional Rich console for output messages
            
        Returns:
            True if successful, False otherwise
        """
        from pathlib import Path
        
        try:
            file_path = Path(output_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as md_file:
                # Write repository header and basic info
                md_file.write(f"# {self.name}\n\n")
                
                # Write statistics section
                md_file.write("## Repository Statistics\n\n")
                for stat_line in self.statistics.strip().split('\n'):
                    if stat_line and '-' in stat_line:
                        if ':' in stat_line:
                            key, value = stat_line.split(':', 1)
                        else:
                            key, value = stat_line.split('-', 1)
                        md_file.write(f"- **{key.strip('- ')}**: {value.strip()}\n")
                md_file.write("\n")
                
                # Write files section with complete data for each file
                md_file.write("## Project Files\n\n")
                
                for i, file in enumerate(self.project_files):
                    # Make a header for each file
                    md_file.write(f"### {i+1}. {file.file_path}\n\n")
                    md_file.write(f"- **File ID**: {file.file_id}\n")
                    md_file.write(f"- **Type**: {'Code File' if isinstance(file, ProjectCodeFile) else 'File'}\n")
                    md_file.write(f"- **Line Count**: {file.line_count}\n")
                    md_file.write(f"- **Description**: {file.description}\n")
                    
                    # If it's a code file, include additional information
                    if isinstance(file, ProjectCodeFile):
                        # Dependencies
                        if file.dependencies:
                            md_file.write("- **Dependencies**:\n")
                            for dep_id in file.dependencies:
                                md_file.write(f"  - {dep_id}\n")
                        else:
                            md_file.write("- **Dependencies**: None\n")
                        
                        # Used by
                        if file.used_by:
                            md_file.write("- **Used By**:\n")
                            for used_id in file.used_by:
                                md_file.write(f"  - {used_id}\n")
                        else:
                            md_file.write("- **Used By**: None\n")
                        
                        # Complexity metrics
                        if file.complexity_metrics:
                            md_file.write("- **Complexity Metrics**:\n")
                            
                            # Cyclomatic complexity
                            if "cyclomatic_complexity" in file.complexity_metrics:
                                cc = file.complexity_metrics["cyclomatic_complexity"]
                                md_file.write("  - **Cyclomatic Complexity**:\n")
                                for cc_key, cc_value in cc.items():
                                    md_file.write(f"    - {cc_key}: {cc_value}\n")
                            
                            # Maintainability index
                            if "maintainability_index" in file.complexity_metrics:
                                mi = file.complexity_metrics["maintainability_index"]
                                md_file.write("  - **Maintainability Index**:\n")
                                for mi_key, mi_value in mi.items():
                                    md_file.write(f"    - {mi_key}: {mi_value}\n")
                            
                            # Code smells
                            if "code_smells" in file.complexity_metrics and file.complexity_metrics["code_smells"]:
                                smells = file.complexity_metrics["code_smells"]
                                md_file.write("  - **Code Smells**:\n")
                                for smell in smells:
                                    md_file.write(f"    - Type: {smell.get('type', 'Unknown')}, Location: {smell.get('location', 'Unknown')}\n")
                                    if "details" in smell:
                                        md_file.write(f"      Details: {smell['details']}\n")
                    
                    # Include the complete file content
                    md_file.write("\n**Content**:\n")
                    md_file.write("```\n")
                    md_file.write(file.content)
                    md_file.write("\n```\n\n")
                    
                    # Add a separator between files
                    md_file.write("---\n\n")
                
                # Add overall statistics as a summary at the end
                md_file.write("## Summary\n\n")
                md_file.write(f"- **Total Files**: {len(self.project_files)}\n")
                md_file.write(f"- **Code Files**: {len([f for f in self.project_files if isinstance(f, ProjectCodeFile)])}\n")
                md_file.write(f"- **Regular Files**: {len([f for f in self.project_files if not isinstance(f, ProjectCodeFile)])}\n")
                
                # Calculate total lines of code
                total_lines = sum(f.line_count for f in self.project_files)
                md_file.write(f"- **Total Lines of Code**: {total_lines}\n")
            
            log.write(f"\n[green]Repository data saved to {output_path}[/green]")
            
            return True
        except Exception as e:
            log.write(f"\n[red]Error saving repository data to Markdown: {str(e)}[/red]")
            import traceback
            log.write(f"\n[red]{traceback.format_exc()}[/red]")
            return False

@flock_type
class UserStory(BaseModel):
    user_story_id: str = Field(..., description="Unique identifier for the user story")
    status: Literal["active", "created", "done"] = Field(..., description="Status of the user story")
    description: str = Field(..., description="Description of the user story")
    definition_of_done: list[str] = Field(..., description="List of criteria for the user story to be considered done")
    tasks: list[str] = Field(..., description="List of task ids that are part of this user story")
    story_points: int = Field(..., description="Number of story points for the user story")
    dependencies: list[str] = Field(..., description="List of user story ids that must be completed before this one")
    used_by: list[str] = Field(..., description="List of user story ids that depend on this one")

@flock_type
class Task(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the task")
    status: Literal["active", "created", "done"] = Field(..., description="Status of the task")
    acceptance_criteria: list[str] = Field(..., description="List of acceptance criteria for the task")
    description: str = Field(..., description="Description of the task")
    estimated_lines_of_code: int = Field(..., description="Estimated number of lines of code for the task")
    dependencies: list[str] = Field(..., description="List of task ids that must be completed before this one")
    used_by: list[str] = Field(..., description="List of task ids that depend on this one")

@flock_type
class ToDoItem(BaseModel):
    todo_id: str = Field(..., description="Unique identifier for the todo item")
    user_story_id: str = Field(..., description="Unique identifier for the user story")
    task_id: str = Field(..., description="Unique identifier for the task")
    cli_command_linux: str | None = Field(..., description="valid CLI command to be executed on linux")
    cli_command_windows: str | None = Field(..., description="valid CLI command to be executed on windows")
    cli_command_macos: str | None = Field(..., description="valid CLI command to be executed on macos")
    file_content: str | None = Field(..., description="Complete content of the file if action is create_file or update_file")
    description: str = Field(..., description="Description and/or reasoning of the todo item")

@flock_type
class TaskAndToDoItemList(BaseModel):
    tasks: list[Task] = Field(..., description="List of tasks")
    todo_items: list[ToDoItem] = Field(..., description="List of todo items")
    



@flock_type
class Project(BaseModel):
    name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Description of the project")
    implementation_plan: str = Field(..., description="High Level Implementation plan for the project in beautiful markdown")
    readme: str = Field(..., description="README.md file for the project in beautiful markdown")
    requirements: list[str] = Field(..., description="List of feature requirements for the project")
    tech_stack: list[str] = Field(..., description="List of technologies used in the project")
    user_stories: list[UserStory] | None = Field(..., description="List of user stories for the project")
    # tasks: list[Task]| None = Field(..., description="List of tasks for the project")
    # project_files: list[ProjectFile | ProjectCodeFile] = Field(..., description="Output data of the project")

    def render_summary(self) -> None:
        """
        Render a summary of the project in a beautiful format.
        
        Args:
            console: The Rich console instance to use for output
        """
        log.write("\n")
        log.write(f"[bold blue]{self.name}")
        log.write("\n")
        log.write(self.description)
        log.write("\n")

        log.write(Markdown(self.implementation_plan))
        log.write("\n")
        log.write(Markdown(self.readme))
        log.write("\n")
        
        # Create a table for requirements
        req_table = Table(title="Project Requirements", box=box.ROUNDED)
        req_table.add_column("Requirement", style="cyan")
        
        for req in self.requirements:
            req_table.add_row(req)
            
        log.write(req_table)
        log.write("\n")
        
        # Create a table for tech stack
        tech_table = Table(title="Technology Stack", box=box.ROUNDED)
        tech_table.add_column("Technology", style="green")
        
        for tech in self.tech_stack:
            tech_table.add_row(tech)
            
        log.write(tech_table)
        log.write("\n")
        
        # Summary of user stories and tasks
        if self.user_stories:
            log.write("\n")
            log.write("[bold cyan]User Stories")
            log.write(f"\n[bold]Total User Stories:[/bold] {len(self.user_stories)}")
            for user_story in self.user_stories:
                log.write(f"\n[bold]User Story:[/bold] {user_story.user_story_id}")
                log.write(f"[bold]Description:[/bold] {user_story.description}")
                log.write(f"[bold]Definition of Done:[/bold] {user_story.definition_of_done}")
                #console.print(f"[bold]Tasks:[/bold] {user_story.tasks}")
                log.write(f"[bold]Story Points:[/bold] {user_story.story_points}")
        
        # if self.tasks:
        #     console.print("\n")
        #     console.rule("[bold cyan]Tasks")
        #     console.print(f"\n[bold]Total Tasks:[/bold] {len(self.tasks)}")
        #     for task in self.tasks:
        #         console.print(f"\n[bold]Task:[/bold] {task.task_id}")
        #         console.print(f"[bold]Description:[/bold] {task.description}")
        #         console.print(f"[bold]Acceptance Criteria:[/bold] {task.acceptance_criteria}")
        #         console.print(f"[bold]Estimated Lines of Code:[/bold] {task.estimated_lines_of_code}")
        #         console.print(f"[bold]Dependencies:[/bold] {task.dependencies}")
        #         console.print(f"[bold]Used By:[/bold] {task.used_by}")
        
        # # Summary of files
        # console.print("\n")
        # console.rule("[bold cyan]Files")
        # console.print(f"\n[bold]Total Files:[/bold] {len(self.project_files)}")
        
        # console.rule("[bold cyan]End of Project Summary")


    
