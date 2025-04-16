# src/pilot_rules/collector/analysis.py
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Import utility function - use relative import within the package
from flock_flightplan.cli.utils import (
    print_warning,
    print_success,
    print_subheader,
)
from textual.widgets import RichLog
log : RichLog = None

def set_app_log(log_component):
    """Set the app's RichLog component for output"""
    global log
    log = log_component


# --- Python Component Extraction ---
def extract_python_components(file_path: str) -> Dict[str, Any]:
    """Extract classes, functions, and imports from Python files."""
    components = {"classes": [], "functions": [], "imports": [], "docstring": None}

    # Ensure it's a python file before trying to parse
    if not file_path.lower().endswith(".py"):
        return components  # Return empty structure for non-python files

    try:
        # Read with error handling for encoding issues
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        tree = ast.parse(content)

        # Extract module docstring
        components["docstring"] = ast.get_docstring(
            tree
        )  # Returns None if no docstring

        # Extract top-level classes and functions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "methods": [
                        m.name
                        for m in node.body
                        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ],
                }
                components["classes"].append(class_info)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # We consider all functions directly under the module body as "top-level" here
                func_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    # Simplified arg extraction (just names)
                    "args": [arg.arg for arg in node.args.args],
                }
                components["functions"].append(func_info)

        # Extract all imports (simplified representation)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Store 'import x' or 'import x as y'
                    components["imports"].append(
                        f"import {alias.name}"
                        + (f" as {alias.asname}" if alias.asname else "")
                    )
            elif isinstance(node, ast.ImportFrom):
                module_part = node.module or ""
                level_dots = "." * node.level
                # Store 'from .mod import x' or 'from mod import x as y'
                imported_names = []
                for alias in node.names:
                    name_part = alias.name
                    if alias.asname:
                        name_part += f" as {alias.asname}"
                    imported_names.append(name_part)

                components["imports"].append(
                    f"from {level_dots}{module_part} import {', '.join(imported_names)}"
                )

    except SyntaxError as e:
        print_warning(
            f"Could not parse Python components in [cyan]{file_path}[/cyan] due to SyntaxError: [red]{e}[/red]"
        )
    except Exception as e:
        print_warning(
            f"Could not parse Python components in [cyan]{file_path}[/cyan]: [red]{e}[/red]"
        )

    return components


# --- Dependency Analysis ---


def get_module_prefixes(module_name: str) -> List[str]:
    """
    Generate all possible module prefixes for a given module name.
    For example, 'a.b.c' would return ['a.b.c', 'a.b', 'a']
    """
    parts = module_name.split(".")
    return [".".join(parts[:i]) for i in range(len(parts), 0, -1)]


def analyze_code_dependencies(files: List[str]) -> Dict[str, Set[str]]:
    """Analyze dependencies between Python files based on imports."""
    # Filter to only analyze python files within the provided list
    python_files = {f for f in files if f.lower().endswith(".py")}
    if not python_files:
        return {}  # No Python files to analyze

    dependencies: Dict[str, Set[str]] = {file: set() for file in python_files}
    module_map: Dict[str, str] = {}  # Map potential module names to absolute file paths
    project_root = (
        Path.cwd().resolve()
    )  # Assume CWD is project root for relative imports

    # --- Build Module Map (heuristic) ---
    # Map files within the project to their potential Python module paths
    for file_path_str in python_files:
        file_path = Path(file_path_str).resolve()
        try:
            # Attempt to create a module path relative to the project root
            relative_path = file_path.relative_to(project_root)
            parts = list(relative_path.parts)
            module_name = None
            if parts[-1] == "__init__.py":
                module_parts = parts[:-1]
                if module_parts:  # Avoid mapping root __init__.py as empty string
                    module_name = ".".join(module_parts)
            elif parts[-1].endswith(".py"):
                module_parts = parts[:-1] + [parts[-1][:-3]]  # Remove .py
                module_name = ".".join(module_parts)

            if module_name:
                # console.print(f"[dim]Mapping module '{module_name}' to '{file_path_str}'[/dim]") # Debug
                module_map[module_name] = file_path_str

        except ValueError:
            # File is outside the assumed project root, less reliable mapping
            # Map only by filename stem if not already mapped? Risky.
            # console.print(f"[dim]Debug: File {file_path_str} is outside project root {project_root}[/dim]")
            pass

    # --- Analyze Imports in Each File ---
    for file_path_str in python_files:
        file_path = Path(file_path_str).resolve()
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            tree = ast.parse(code)

            for node in ast.walk(tree):
                imported_module_str = None
                target_file: Optional[str] = None

                # Handle 'import x' or 'import x.y'
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_module_str = alias.name
                        # Check full name and prefixes against our map
                        for prefix in get_module_prefixes(imported_module_str):
                            if prefix in module_map:
                                target_file = module_map[prefix]
                                # Ensure the target is actually one of the collected python files
                                if (
                                    target_file in python_files
                                    and target_file != file_path_str
                                ):
                                    dependencies[file_path_str].add(target_file)
                                break  # Found the longest matching prefix

                # Handle 'from x import y' or 'from .x import y'
                elif isinstance(node, ast.ImportFrom):
                    level = node.level
                    module_base = node.module or ""

                    if level == 0:  # Absolute import: 'from package import module'
                        imported_module_str = module_base
                        for prefix in get_module_prefixes(imported_module_str):
                            if prefix in module_map:
                                target_file = module_map[prefix]
                                if (
                                    target_file in python_files
                                    and target_file != file_path_str
                                ):
                                    dependencies[file_path_str].add(target_file)
                                break
                    else:  # Relative import: 'from . import x', 'from ..y import z'
                        current_dir = file_path.parent
                        base_path = current_dir
                        # Navigate up for '..' (level 2 means one level up, etc.)
                        for _ in range(level - 1):
                            base_path = base_path.parent

                        # Try to resolve the relative path
                        relative_module_parts = (
                            module_base.split(".") if module_base else []
                        )
                        target_path_base = base_path
                        for part in relative_module_parts:
                            target_path_base = target_path_base / part

                        # Check if the resolved path corresponds to a known file/module
                        # Check 1: Is it a directory with __init__.py?
                        init_py_path = (target_path_base / "__init__.py").resolve()
                        init_py_str = str(init_py_path)
                        if init_py_str in python_files and init_py_str != file_path_str:
                            dependencies[file_path_str].add(init_py_str)
                            target_file = init_py_str  # Mark as found

                        # Check 2: Is it a .py file directly?
                        module_py_path = target_path_base.with_suffix(".py").resolve()
                        module_py_str = str(module_py_path)
                        if (
                            not target_file
                            and module_py_str in python_files
                            and module_py_str != file_path_str
                        ):
                            dependencies[file_path_str].add(module_py_str)
                            target_file = module_py_str

                        # Note: This relative import resolution is basic and might miss complex cases.
                        # We are primarily checking if the base module path (e.g., `.`, `..utils`) exists.

        except SyntaxError as e:
            print_warning(
                f"Skipping import analysis in [cyan]{file_path_str}[/cyan] due to SyntaxError: [red]{e}[/red]"
            )
        except Exception as e:
            print_warning(
                f"Could not analyze imports in [cyan]{file_path_str}[/cyan]: [red]{e}[/red]"
            )

    return dependencies


# --- Pattern Detection ---


def get_common_patterns(files: List[str]) -> Dict[str, Any]:
    """Identify common code patterns across the repository."""
    patterns = {"python_patterns": {}}

    # Get all Python files
    python_files = [f for f in files if f.lower().endswith(".py")]
    if not python_files:
        return patterns  # No Python files to analyze

    # --- Python Import Patterns ---
    all_imports: Dict[str, int] = {}
    file_imports: Dict[str, List[str]] = {}

    # Basic frameworks imports to check for
    frameworks = {
        "Django": ["django", "django.db", "django.http", "django.urls", "django.views"],
        "Flask": ["flask", "flask_restful", "flask_sqlalchemy"],
        "FastAPI": ["fastapi"],
        "SQLAlchemy": ["sqlalchemy"],
        "PyTorch": ["torch"],
        "TensorFlow": ["tensorflow", "tf"],
        "Pandas": ["pandas"],
        "Numpy": ["numpy", "np"],
        "Pytest": ["pytest"],
        "Unittest": ["unittest"],
    }

    # Track framework detections
    framework_evidence: Dict[str, str] = {}

    for file_path in python_files:
        # Extract components including imports
        components = extract_python_components(file_path)
        imports = components.get("imports", [])

        # Store all the raw imports
        file_imports[file_path] = imports

        # Process each import line
        for imp in imports:
            # Normalize import line by removing "as X" aliases
            # This helps count semantically identical imports
            base_import = imp.split(" as ")[0].strip()
            all_imports[base_import] = all_imports.get(base_import, 0) + 1

            # Check for framework indicators
            for framework, indicators in frameworks.items():
                for indicator in indicators:
                    if indicator in imp.split()[1]:  # Check the module part
                        if framework not in framework_evidence:
                            framework_evidence[framework] = (
                                f"Found import '{imp}' in {Path(file_path).name}"
                            )
                        break

    # Sort by frequency
    common_imports = sorted(all_imports.items(), key=lambda x: x[1], reverse=True)
    patterns["python_patterns"]["common_imports"] = common_imports

    # Add framework detections if any
    if framework_evidence:
        patterns["python_patterns"]["framework_patterns"] = framework_evidence

    # Important: try/except to avoid failures during pattern detection
    # This is analysis code, shouldn't crash the report generation
    try:
        # Common file patterns based on naming conventions
        repository_patterns = {}
        # ... extend with more pattern detection as needed...

        # Add to patterns dict
        patterns.update(repository_patterns)
    except Exception:
        # Less prominent warning since this is enhancement, not core functionality
        # print(f"Warning: Could not analyze patterns in {file_path}: {e}") # Can be noisy
        pass

    return patterns


# --- Key File Identification ---


def find_key_files(files: List[str], dependencies: Dict[str, Set[str]]) -> List[str]:
    """
    Identify key files in the repository based on several heuristic factors.
    - Dependency count (how many files depend on this one)
    - Naming convention (e.g., main.py, __init__.py)
    - File size and location
    """
    print_subheader("Scoring files to identify key ones", "cyan")

    if not files:
        return []

    # 1. Prepare scoring dict
    scores: Dict[str, float] = {file: 0.0 for file in files}

    # 2. Score based on file naming and key locations
    key_names = ["main", "app", "core", "index", "server", "engine", "controller"]
    for file in files:
        file_path = Path(file)
        filename_stem = file_path.stem.lower()

        # Key names in filename get points
        for key in key_names:
            if key == filename_stem:
                scores[file] += 5.0  # Exact match
            elif key in filename_stem:
                scores[file] += 2.0  # Partial match

        # Special files
        if filename_stem == "__init__":
            scores[file] += 1.0
        if filename_stem == "__main__":
            scores[file] += 3.0

        # Files in root directories are often important
        try:
            rel_path = file_path.relative_to(Path.cwd())
            depth = len(rel_path.parts)
            if depth <= 2:  # In root or direct subdirectory
                scores[file] += 3.0 / depth  # More points for less depth
        except ValueError:
            # File outside cwd, skip this bonus
            pass

        # Size can indicate importance (within reason)
        try:
            size = file_path.stat().st_size
            # Log scale to avoid over-prioritizing large files
            if size > 0:
                import math

                size_score = min(3.0, math.log(size) / 3)
                scores[file] += size_score
        except OSError:
            pass

    # 3. Dependency analysis (Python)
    # Calculate how many files depend on each file (reversed dependency graph)
    dependents: Dict[str, Set[str]] = {file: set() for file in files}
    for source, targets in dependencies.items():
        for target in targets:
            if target in dependents:
                dependents[target].add(source)

    # Score based on dependent count (files that import this file)
    for file, deps in dependents.items():
        count = len(deps)
        if count > 0:
            # More weight for dependencies
            scores[file] += count * 2.0
            # console.print(f"  Score bump (deps): {Path(file).name} +{count * 2.0} (depended by {count})")

    # 4. Select top files based on scores
    # Calculate a reasonable number based on repository size
    num_key_files = min(
        10, max(3, int(len(files) * 0.1))
    )  # 10% but at least 3, at most 10

    # Sort files by score (descending) and select top N
    top_files = sorted(files, key=lambda f: scores.get(f, 0), reverse=True)[
        :num_key_files
    ]

    print_success(f"Selected top {num_key_files} files as key files.")

    # Debug info (commented out in production)
    # for i, f in enumerate(top_files):
    #      console.print(f"  {i+1}. {Path(f).name}: {scores.get(f, 0.0):.2f}")

    return top_files
