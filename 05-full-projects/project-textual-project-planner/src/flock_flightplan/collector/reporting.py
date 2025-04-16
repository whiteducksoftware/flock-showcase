# src/pilot_rules/collector/reporting.py
import datetime
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

# Import functions from sibling modules
from flock_flightplan.cli.utils import (
    get_file_metadata,
    print_header,
    print_success,
    print_warning,
    print_error,
    print_subheader,
)
from flock_flightplan.collector.analysis import extract_python_components  # Import needed analysis functions
from flock_flightplan.collector.metrics import calculate_file_metrics  # Import the new metrics module
from flock_flightplan.model import Repository, ProjectFile, ProjectCodeFile
from textual.widgets import RichLog

log : RichLog = None
def set_app_log(log_component):
    """Set the app's RichLog component for output"""
    global log
    log = log_component
# --- Folder Tree Generation ---
# (generate_folder_tree function remains the same as the previous version)
def generate_folder_tree(root_folder_path: Path, included_files: List[str]) -> str:
    """Generate an ASCII folder tree representation for included files relative to a root."""
    tree_lines: List[str] = []
    included_files_set = {Path(f).resolve() for f in included_files}  # Absolute paths

    # Store relative paths from the root_folder_path for display and structure building
    # We only include paths *under* the specified root_folder_path in the tree display
    included_relative_paths: Dict[Path, bool] = {}  # Map relative path -> is_file
    all_parent_dirs: Set[Path] = set()  # Set of relative directory paths

    for abs_path in included_files_set:
        try:
            rel_path = abs_path.relative_to(root_folder_path)
            included_relative_paths[rel_path] = True  # Mark as file
            # Add all parent directories of this file
            parent = rel_path.parent
            while parent != Path("."):  # Stop before adding '.' itself
                if (
                    parent not in included_relative_paths
                ):  # Avoid marking parent as file if dir listed later
                    included_relative_paths[parent] = False  # Mark as directory
                all_parent_dirs.add(parent)
                parent = parent.parent
        except ValueError:
            # File is not under the root_folder_path, skip it in this tree view
            continue

    # Combine files and their necessary parent directories
    sorted_paths = sorted(included_relative_paths.keys(), key=lambda p: p.parts)

    # --- Tree building logic ---
    # Based on relative paths and depth
    tree_lines.append(f"{root_folder_path.name}/")  # Start with the root dir name

    entries_by_parent: Dict[
        Path, List[Tuple[Path, bool]]
    ] = {}  # parent -> list of (child, is_file)
    for rel_path, is_file in included_relative_paths.items():
        parent = rel_path.parent
        if parent not in entries_by_parent:
            entries_by_parent[parent] = []
        entries_by_parent[parent].append((rel_path, is_file))

    # Sort children within each parent directory
    for parent in entries_by_parent:
        entries_by_parent[parent].sort(
            key=lambda item: (not item[1], item[0].parts)
        )  # Dirs first, then alpha

    processed_paths = set()  # To avoid duplicates if a dir is both parent and included

    def build_tree_recursive(parent_rel_path: Path, prefix: str):
        if parent_rel_path not in entries_by_parent:
            return

        children = entries_by_parent[parent_rel_path]
        for i, (child_rel_path, is_file) in enumerate(children):
            if child_rel_path in processed_paths:
                continue

            is_last = i == len(children) - 1
            connector = "└── " if is_last else "├── "
            entry_name = child_rel_path.name
            display_name = f"{entry_name}{'' if is_file else '/'}"
            tree_lines.append(f"{prefix}{connector}{display_name}")
            processed_paths.add(child_rel_path)

            if not is_file:  # If it's a directory, recurse
                new_prefix = f"{prefix}{'    ' if is_last else '│   '}"
                build_tree_recursive(child_rel_path, new_prefix)

    # Start recursion from the root ('.') relative path
    build_tree_recursive(Path("."), "")

    # Join lines, ensuring the root is handled correctly if empty
    if (
        len(tree_lines) == 1 and not included_relative_paths
    ):  # Only root line, no files/dirs under it
        tree_lines[0] = f"└── {root_folder_path.name}/"  # Adjust prefix for empty tree

    return "\n".join(tree_lines)


# --- Markdown Generation ---
def generate_markdown(
    files: List[str],  # List of absolute paths
    analyzed_extensions: Set[
        str
    ],  # Set of actual extensions found (e.g., '.py', '.js')
    dependencies: Dict[str, Set[str]],  # Python dependencies
    patterns: Dict[str, Any],  # Detected patterns
    key_files: List[str],  # List of absolute paths for key files
    output_path: Path,
    root_folder_display: str = ".",  # How to display the root in summary/tree
) -> None:
    """Generate a comprehensive markdown document about the codebase."""
    print_header("Generating Report", "green")
    log.write(f"Output file: [cyan]{output_path}[/cyan]")
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)  # Ensure output directory exists
    report_base_path = (
        Path.cwd()
    )  # Use CWD as the base for relative paths in the report

    has_python_files = ".py" in analyzed_extensions

    with open(output_path, "w", encoding="utf-8") as md_file:
        # --- Header ---
        md_file.write("# Code Repository Analysis\n\n")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
            :-3
        ]  # ms precision
        md_file.write(f"Generated on {timestamp}\n\n")

        # --- Repository Summary ---
        md_file.write("## Repository Summary\n\n")
        ext_list_str = (
            ", ".join(sorted(list(analyzed_extensions)))
            if analyzed_extensions
            else "N/A"
        )
        md_file.write(f"- **Extensions analyzed**: `{ext_list_str}`\n")
        md_file.write(f"- **Number of files analyzed**: {len(files)}\n")
        md_file.write(
            f"- **Analysis Root (for display)**: `{root_folder_display}`\n"
        )  # Indicate the main perspective

        total_lines = 0
        if files:
            try:
                total_lines = sum(
                    get_file_metadata(f).get("line_count", 0) for f in files
                )
            except Exception as e:
                print_warning(f"Could not calculate total lines accurately: {e}")
                total_lines = "N/A"
        else:
            total_lines = 0
        md_file.write(f"- **Total lines of code (approx)**: {total_lines}\n\n")

        # --- Project Structure ---
        md_file.write("## Project Structure (Relative View)\n\n")
        md_file.write("```\n")
        try:
            root_for_tree = Path(root_folder_display).resolve()
            if root_for_tree.is_dir():
                md_file.write(generate_folder_tree(root_for_tree, files))
            else:
                print_warning(
                    f"Display root '{root_folder_display}' not found or not a directory, using CWD for tree."
                )
                md_file.write(generate_folder_tree(report_base_path, files))
        except Exception as tree_err:
            print_error(f"Error generating folder tree: {tree_err}")
            md_file.write(f"Error generating folder tree: {tree_err}")
        md_file.write("\n```\n\n")

        # --- Key Files Section ---
        md_file.write("## Key Files\n\n")
        if key_files:
            md_file.write(
                "These files appear central based on dependencies, naming, and size:\n\n"
            )
            for file_abs_path in key_files:
                try:
                    rel_path = str(Path(file_abs_path).relative_to(report_base_path))
                except ValueError:
                    rel_path = file_abs_path  # Fallback to absolute if not relative

                md_file.write(f"### {rel_path}\n\n")
                metadata = get_file_metadata(file_abs_path)
                md_file.write(f"- **Lines**: {metadata.get('line_count', 'N/A')}\n")
                md_file.write(
                    f"- **Size**: {metadata.get('size_bytes', 0) / 1024:.2f} KB\n"
                )
                md_file.write(
                    f"- **Last modified**: {metadata.get('last_modified', 'Unknown')}\n"
                )

                # Dependency info (Python only)
                if has_python_files and file_abs_path in dependencies:
                    dependent_files_abs = {
                        f for f, deps in dependencies.items() if file_abs_path in deps
                    }
                    if dependent_files_abs:
                        md_file.write(
                            f"- **Used by**: {len(dependent_files_abs)} other analyzed Python file(s)\n"
                        )

                # Python component analysis
                if file_abs_path.lower().endswith(".py"):
                    components = extract_python_components(
                        file_abs_path
                    )  # Use imported function
                    if components.get("docstring"):
                        docstring_summary = (
                            components["docstring"].strip().split("\n", 1)[0]
                        )[:150]
                        md_file.write(
                            f"\n**Description**: {docstring_summary}{'...' if len(components['docstring']) > 150 else ''}\n"
                        )
                    if components.get("classes"):
                        md_file.write("\n**Classes**:\n")
                        for cls in components["classes"][:5]:
                            md_file.write(
                                f"- `{cls['name']}` ({len(cls['methods'])} methods)\n"
                            )
                        if len(components["classes"]) > 5:
                            md_file.write("- ... (and more)\n")
                    if components.get("functions"):
                        md_file.write("\n**Functions**:\n")
                        for func in components["functions"][:5]:
                            md_file.write(f"- `{func['name']}(...)`\n")
                        if len(components["functions"]) > 5:
                            md_file.write("- ... (and more)\n")

                # ==================================
                # --- Include FULL File Content ---
                md_file.write("\n**Content**:\n")  # Changed from "Content Snippet"
                file_ext = Path(file_abs_path).suffix.lower()
                lang_hint = file_ext.lstrip(".") if file_ext else ""
                md_file.write(f"```{lang_hint}\n")
                try:
                    with open(
                        file_abs_path, "r", encoding="utf-8", errors="ignore"
                    ) as code_file:
                        # Read the entire file content
                        full_content = code_file.read()
                        md_file.write(full_content)
                        # Ensure a newline at the end of the code block if file doesn't have one
                        if not full_content.endswith("\n"):
                            md_file.write("\n")
                except Exception as e:
                    md_file.write(f"Error reading file: {e}\n")
                md_file.write("```\n\n")

        # --- Other Markdown Files Section ---
        md_file.write("## Other Files\n\n")
        md_file.write("This section includes content of all other analyzed files that aren't in the key files list.\n\n")
        
        # Filter out key files
        other_files = [f for f in files if f not in key_files]
        
        if other_files:
            for file_abs_path in other_files:
                try:
                    rel_path = str(Path(file_abs_path).relative_to(report_base_path))
                except ValueError:
                    rel_path = file_abs_path  # Fallback to absolute if not relative

                md_file.write(f"### {rel_path}\n\n")
                metadata = get_file_metadata(file_abs_path)
                md_file.write(f"- **Lines**: {metadata.get('line_count', 'N/A')}\n")
                md_file.write(
                    f"- **Size**: {metadata.get('size_bytes', 0) / 1024:.2f} KB\n"
                )
                md_file.write(
                    f"- **Last modified**: {metadata.get('last_modified', 'Unknown')}\n"
                )

                # Include full file content
                md_file.write("\n**Content**:\n")
                file_ext = Path(file_abs_path).suffix.lower()
                lang_hint = file_ext.lstrip(".") if file_ext else ""
                md_file.write(f"```{lang_hint}\n")
                try:
                    with open(
                        file_abs_path, "r", encoding="utf-8", errors="ignore"
                    ) as code_file:
                        # Read the entire file content
                        full_content = code_file.read()
                        md_file.write(full_content)
                        # Ensure a newline at the end of the code block if file doesn't have one
                        if not full_content.endswith("\n"):
                            md_file.write("\n")
                except Exception as e:
                    md_file.write(f"Error reading file: {e}\n")
                md_file.write("```\n\n")
        else:
            md_file.write("No additional files found.\n\n")

        # --- Python Dependency Analysis (if applicable) ---
        if has_python_files and dependencies:
            md_file.write("## Python Dependencies\n\n")
            md_file.write(
                "This section shows Python modules and their dependencies within the project.\n\n"
            )

            dep_count = sum(len(deps) for deps in dependencies.values())
            if dep_count > 0:
                md_file.write("### Internal Dependencies\n\n")
                md_file.write("```mermaid\ngraph TD;\n")
                # Generate mermaid.js compatible graph nodes and edges
                node_ids = {}
                for i, file_path in enumerate(dependencies.keys()):
                    try:
                        rel_path = str(Path(file_path).relative_to(report_base_path))
                    except ValueError:
                        rel_path = str(
                            Path(file_path).name
                        )  # Just use filename if not relative
                    node_id = f"F{i}"
                    node_ids[file_path] = node_id
                    # Escape any problematic characters in label
                    label = rel_path.replace('"', '\\"')
                    md_file.write(f'    {node_id}["{label}"];\n')

                # Add edges for dependencies
                for file_path, deps in dependencies.items():
                    if not deps:
                        continue
                    source_id = node_ids[file_path]
                    for dep in deps:
                        if dep in node_ids:  # Ensure dep is in our analyzed files
                            target_id = node_ids[dep]
                            md_file.write(f"    {source_id} --> {target_id};\n")
                md_file.write("```\n\n")

                # Add plain text dependency list as fallback
                md_file.write("### Dependency List (Plain Text)\n\n")
                for file_path, deps in dependencies.items():
                    if not deps:
                        continue  # Skip files with no dependencies
                    try:
                        rel_path = str(Path(file_path).relative_to(report_base_path))
                    except ValueError:
                        rel_path = file_path
                    md_file.write(f"- **{rel_path}** depends on:\n")
                    for dep in sorted(deps):
                        try:
                            dep_rel = str(Path(dep).relative_to(report_base_path))
                        except ValueError:
                            dep_rel = dep
                        md_file.write(f"  - {dep_rel}\n")

        # --- Common Code Patterns ---
        if patterns and patterns.get("python_patterns"):
            py_patterns = patterns["python_patterns"]
            if py_patterns:
                md_file.write("## Common Code Patterns\n\n")
                md_file.write("### Python Patterns\n\n")

                if py_patterns.get("common_imports"):
                    md_file.write("#### Common Imports\n\n")
                    for imp, count in py_patterns["common_imports"][:10]:
                        md_file.write(f"- `{imp}` ({count} files)\n")
                    if len(py_patterns["common_imports"]) > 10:
                        md_file.write("- *(and more...)*\n")
                    md_file.write("\n")

                if py_patterns.get("framework_patterns"):
                    md_file.write("#### Framework Detection\n\n")
                    for framework, evidence in py_patterns[
                        "framework_patterns"
                    ].items():
                        md_file.write(f"- **{framework}**: {evidence}\n")
                    md_file.write("\n")

    # Final success message
    print_success(f"Markdown report generated successfully at '{output_path}'")


# --- Repository Object Generation ---
def generate_repository(
    files: List[str],  # List of absolute paths
    analyzed_extensions: Set[str],  # Set of actual extensions found (e.g., '.py', '.js')
    dependencies: Dict[str, Set[str]],  # Python dependencies
    patterns: Dict[str, Any],  # Detected patterns
    key_files: List[str],  # List of absolute paths for key files
    repo_name: str = "Repository Analysis",
    root_folder_display: str = ".",  # How to display the root in summary/tree
    calculate_metrics: bool = False,  # New parameter to control metrics calculation
) -> Repository:
    """Generate a Repository object with analyzed code structure and content."""
    print_header("Generating Repository Object", "green")
    report_base_path = Path.cwd()  # Use CWD as the base for relative paths in the report

    has_python_files = ".py" in analyzed_extensions

    # Generate statistics
    ext_list_str = ", ".join(sorted(list(analyzed_extensions))) if analyzed_extensions else "N/A"
    total_files = len(files)
    
    total_lines = 0
    if files:
        try:
            total_lines = sum(get_file_metadata(f).get("line_count", 0) for f in files)
        except Exception as e:
            print_warning(f"Could not calculate total lines accurately: {e}")
            total_lines = 0
    
    statistics = f"""
- Extensions analyzed: {ext_list_str}
- Number of files analyzed: {total_files}
- Total lines of code (approx): {total_lines}
"""

    # Process files to create ProjectFile objects
    project_files = []
    
    # First create a mapping of absolute paths to file_ids
    file_id_mapping = {}
    for i, file_abs_path in enumerate(files):
        try:
            rel_path = str(Path(file_abs_path).relative_to(report_base_path))
        except ValueError:
            rel_path = file_abs_path  # Fallback to absolute if not relative
        
        file_id = f"file_{i}"
        file_id_mapping[file_abs_path] = file_id
    
    # Pre-calculate metrics for Python files to include in statistics, but only if metrics are enabled
    python_files = [f for f in files if f.lower().endswith('.py')]
    metrics_by_file = {}
    
    if calculate_metrics and python_files:
        print_subheader("Calculating Code Quality Metrics", "blue")
        
        # Track overall metrics
        total_complexity = 0
        files_with_complexity = 0
        total_maintainability = 0
        files_with_maintainability = 0
        complexity_ranks = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        maintainability_ranks = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        total_code_smells = 0
        
        # Calculate metrics for each Python file
        for file_path in python_files:
            metrics = calculate_file_metrics(file_path)
            metrics_by_file[file_path] = metrics
            
            # Aggregate statistics
            cc = metrics.get("cyclomatic_complexity", {})
            if cc and "total" in cc:
                total_complexity += cc["total"]
                files_with_complexity += 1
                if "rank" in cc:
                    complexity_ranks[cc["rank"]] = complexity_ranks.get(cc["rank"], 0) + 1
            
            mi = metrics.get("maintainability_index", {})
            if mi and "value" in mi:
                total_maintainability += mi["value"]
                files_with_maintainability += 1
                if "rank" in mi:
                    maintainability_ranks[mi["rank"]] = maintainability_ranks.get(mi["rank"], 0) + 1
            
            smells = metrics.get("code_smells", [])
            total_code_smells += len(smells)
        
        # Add code quality metrics to statistics
        avg_complexity = total_complexity / files_with_complexity if files_with_complexity > 0 else 0
        avg_maintainability = total_maintainability / files_with_maintainability if files_with_maintainability > 0 else 0
        
        complexity_distribution = ", ".join([f"{rank}: {count}" for rank, count in complexity_ranks.items() if count > 0])
        maintainability_distribution = ", ".join([f"{rank}: {count}" for rank, count in maintainability_ranks.items() if count > 0])
        
        quality_stats = f"""
- Average cyclomatic complexity: {avg_complexity:.2f}
- Complexity distribution: {complexity_distribution}
- Average maintainability index: {avg_maintainability:.2f}
- Maintainability distribution: {maintainability_distribution}
- Total code smells detected: {total_code_smells}
"""
        
        # Add code quality metrics to main statistics if metrics were calculated
        if files_with_complexity > 0 or files_with_maintainability > 0:
            statistics += quality_stats

    # Now create ProjectFile objects with proper dependencies
    for file_abs_path in files:
        try:
            rel_path = str(Path(file_abs_path).relative_to(report_base_path))
        except ValueError:
            rel_path = file_abs_path  # Fallback to absolute if not relative
            
        metadata = get_file_metadata(file_abs_path)
        file_id = file_id_mapping[file_abs_path]
        
        try:
            with open(file_abs_path, "r", encoding="utf-8", errors="ignore") as code_file:
                content = code_file.read()
        except Exception as e:
            print_warning(f"Could not read file content for {rel_path}: {e}")
            content = f"Error reading file: {str(e)}"
        
        # Generate description based on file type
        description = f"File at {rel_path}"
        if file_abs_path.lower().endswith(".py"):
            components = extract_python_components(file_abs_path)
            if components.get("docstring"):
                docstring_summary = components["docstring"].strip().split("\n", 1)[0][:150]
                description = docstring_summary + ('...' if len(components["docstring"]) > 150 else '')
            
            # For Python files, create ProjectCodeFile with dependencies
            file_deps = []
            file_used_by = []
            
            # Find dependencies
            if has_python_files and file_abs_path in dependencies:
                file_deps = [file_id_mapping[dep] for dep in dependencies[file_abs_path] if dep in file_id_mapping]
                
                # Find files that depend on this file
                dependent_files_abs = {f for f, deps in dependencies.items() if file_abs_path in deps}
                file_used_by = [file_id_mapping[dep] for dep in dependent_files_abs if dep in file_id_mapping]
            
            # Use pre-calculated metrics if available, otherwise calculate them now
            complexity_metrics = {}
            if calculate_metrics:
                complexity_metrics = metrics_by_file.get(file_abs_path, {})
                if not complexity_metrics:
                    complexity_metrics = calculate_file_metrics(file_abs_path)
            
            project_file = ProjectCodeFile(
                file_id=file_id,
                description=description,
                file_path=rel_path,
                content=content,
                line_count=metadata.get('line_count', 0),
                dependencies=file_deps,
                used_by=file_used_by,
                complexity_metrics=complexity_metrics
            )
        else:
            # Regular ProjectFile for non-Python files
            project_file = ProjectFile(
                file_id=file_id,
                description=description,
                file_path=rel_path,
                content=content,
                line_count=metadata.get('line_count', 0)
            )
        
        project_files.append(project_file)
    
    # Create and return the Repository object
    repository = Repository(
        name=repo_name,
        statistics=statistics,
        project_files=project_files
    )
    
    print_success(f"Successfully generated Repository object with {len(project_files)} files")
    return repository
