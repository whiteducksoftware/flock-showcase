# src/pilot_rules/collector/__init__.py
"""
Code Collection and Analysis Sub-package.
Provides functionality to scan repositories, analyze code (primarily Python),
and generate Repository objects.
"""

from typing import List, Optional

# Import necessary functions from sibling modules using relative imports
from flock_flightplan.cli import utils
from flock_flightplan.collector import config
from flock_flightplan.collector import discovery
from flock_flightplan.collector import analysis
from flock_flightplan.collector import reporting
from flock_flightplan.collector.config import process_config_and_args
from flock_flightplan.collector.discovery import collect_files
from flock_flightplan.collector.analysis import analyze_code_dependencies, get_common_patterns, find_key_files
from flock_flightplan.collector.reporting import generate_repository
from flock_flightplan.cli.utils import (
    log,
    print_header,
    print_subheader,
    print_success,
    print_warning,
    print_error,
    print_file_stats,
)
from flock_flightplan.model import Repository
from flock_flightplan.model import set_app_log as model_set_app_log
from textual.widgets import RichLog

log : RichLog = None

def set_app_log(log_component):
    """Set the app's RichLog component for output"""
    global log
    log = log_component
    config.set_app_log(log)
    discovery.set_app_log(log)
    analysis.set_app_log(log)
    reporting.set_app_log(log)
    utils.set_app_log(log)
    model_set_app_log(log)

def run_collection(
    include_args: Optional[List[str]],
    exclude_args: Optional[List[str]],
    output_arg: Optional[str] = None,  # Kept for backward compatibility but used to save Repository as JSON
    config_arg: Optional[str] = None,
    repo_name: Optional[str] = None,
    calculate_metrics: bool = False,  # New parameter to control metrics calculation
) -> Repository:
    """
    Main entry point for the code collection process.

    Orchestrates configuration loading, file discovery, analysis, and Repository generation.
    
    Args:
        include_args: List of include patterns in format 'ext1,ext2:./folder'
        exclude_args: List of exclude patterns in format 'py:temp'
        output_arg: Path to output JSON file to save the repository (optional)
        config_arg: Path to optional TOML config file
        repo_name: Name for the repository (default is "Repository Analysis")
        calculate_metrics: Whether to calculate code quality metrics (default is False)
        
    Returns:
        Repository object with analyzed code data
    """
    try:
        # 1. Process Configuration and Arguments
        print_header("Code Collection Process", "magenta")
        final_sources, final_excludes, _ = process_config_and_args(
            include_args=include_args,
            exclude_args=exclude_args,
            output_arg=output_arg,
            config_arg=config_arg,
        )

        # Use provided repo_name or default
        repository_name = repo_name if repo_name else "Repository Analysis"

        # 2. Collect Files based on finalized sources and excludes
        collected_files, actual_extensions = collect_files(
            final_sources, final_excludes
        )

        if not collected_files:
            print_warning("No files found matching the specified criteria.")
            # Return minimal Repository with empty files list
            return Repository(
                name=repository_name,
                statistics="No files found matching the specified criteria.",
                project_files=[]
            )
        else:
            print_success(
                f"Found [bold green]{len(collected_files)}[/bold green] files to include in the analysis."
            )
            ext_list = ", ".join(sorted(list(actual_extensions)))
            log.write(f"File extensions found: [cyan]{ext_list}[/cyan]")

            # Display file statistics in a nice table
            print_file_stats(collected_files, "Collection Statistics")

        # 3. Perform Analysis (Conditional based on files found)
        dependencies = {}
        patterns = {}
        key_files = []

        # Only run Python-specific analysis if .py files are present
        has_python_files = ".py" in actual_extensions
        if has_python_files:
            print_subheader("Analyzing Python Dependencies", "blue")
            dependencies = analyze_code_dependencies(collected_files)
            print_subheader("Identifying Code Patterns", "blue")
            patterns = get_common_patterns(collected_files)
        else:
            print_warning("Skipping Python-specific analysis (no .py files found).")

        # Find key files (uses heuristics applicable to various file types)
        if collected_files:
            # Note: find_key_files now has its own print_subheader call
            key_files = find_key_files(collected_files, dependencies)  # Pass all files

        # 4. Generate Repository Object
        repository = generate_repository(
            files=collected_files,
            analyzed_extensions=actual_extensions,
            dependencies=dependencies,
            patterns=patterns,
            key_files=key_files,
            repo_name=repository_name,
            root_folder_display=".",  # Or derive from sources if needed
            calculate_metrics=calculate_metrics,  # Pass the metrics flag
        )
        
        # 5. Save Repository as JSON if output_arg is provided
        if output_arg:
            import json
            from pathlib import Path
            
            try:
                # Convert repository to dict and save as JSON
                repo_dict = repository.dict()
                output_path = Path(output_arg)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(repo_dict, f, indent=2)
                print_success(f"Repository data saved to {output_path}")
            except Exception as e:
                print_error(f"Error saving repository data: {str(e)}")
        
        return repository

    except ValueError as e:
        # Configuration or argument parsing errors
        print_error(f"Configuration Error: {e}", 1)
        raise
    except Exception as e:
        # Catch-all for unexpected errors during collection/analysis/reporting
        print_error(f"An unexpected error occurred: {e}", 1)
        import traceback
        traceback.print_exc()
        raise

# Alias for backward compatibility
generate_repository_from_files = run_collection
