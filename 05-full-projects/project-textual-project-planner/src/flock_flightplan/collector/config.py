# src/pilot_rules/collector/config.py
import tomli
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from flock_flightplan.cli.utils import (
    print_subheader,
)
from textual.widgets import RichLog

DEFAULT_OUTPUT_FILENAME = "repository_analysis.md"
DEFAULT_INCLUDE_SPEC = "py:."  # Default to python files in current dir

log : RichLog = None



def set_app_log(log_component):
    """Set the app's RichLog component for output"""
    global log
    log = log_component

def parse_include_exclude_args(args: Optional[List[str]]) -> List[Dict[str, Any]]:
    """Parses include/exclude arguments like 'py,js:src' or '*:temp'."""
    parsed = []
    if not args:
        return parsed

    for arg in args:
        if ":" not in arg:
            raise ValueError(
                f"Invalid include/exclude format: '{arg}'. Expected 'EXTS:PATH' or '*:PATTERN'."
            )

        exts_str, path_pattern = arg.split(":", 1)
        extensions = [
            ext.strip().lower().lstrip(".")
            for ext in exts_str.split(",")
            if ext.strip()
        ]
        if not extensions:
            raise ValueError(f"No extensions specified in '{arg}'. Use '*' for all.")

        # Use '*' as a special marker for all extensions
        if "*" in extensions:
            extensions = ["*"]

        # Normalize path pattern to use forward slashes for consistency
        # Keep it relative for now, resolve later if needed
        path_pattern = Path(path_pattern).as_posix()

        parsed.append(
            {
                "extensions": extensions,  # List of extensions (lowercase, no dot), or ['*']
                "pattern": path_pattern,  # Path or pattern string (relative or absolute)
            }
        )
    return parsed


def load_config_from_toml(
    config_path: Path,
) -> Tuple[List[Dict], List[Dict], Optional[str]]:
    """Loads sources, excludes, and output path from a TOML file."""
    config_sources = []
    config_excludes = []
    config_output = None

    print_subheader(f"Loading configuration from: [cyan]{config_path}[/cyan]")
    try:
        with open(config_path, "rb") as f:
            config_data = tomli.load(f)

        # --- Parse sources ---
        raw_sources = config_data.get("source", [])
        if not isinstance(raw_sources, list):
            raise ValueError("Invalid config: 'source' must be an array of tables.")

        for i, src_table in enumerate(raw_sources):
            if not isinstance(src_table, dict):
                raise ValueError(
                    f"Invalid config: Item {i} in 'source' array is not a table."
                )

            exts = src_table.get("exts", ["*"])  # Default to all if not specified
            root = src_table.get("root", ".")
            exclude_patterns = src_table.get(
                "exclude", []
            )  # Excludes within a source block

            if not isinstance(exts, list) or not all(isinstance(e, str) for e in exts):
                raise ValueError(
                    f"Invalid config: 'exts' must be a list of strings in source #{i + 1}"
                )
            if not isinstance(root, str):
                raise ValueError(
                    f"Invalid config: 'root' must be a string in source #{i + 1}."
                )
            if not isinstance(exclude_patterns, list) or not all(
                isinstance(p, str) for p in exclude_patterns
            ):
                raise ValueError(
                    f"Invalid config: 'exclude' must be a list of strings in source #{i + 1}"
                )

            # Normalize extensions: lowercase, no leading dot
            normalized_exts = [e.lower().lstrip(".") for e in exts]
            if "*" in normalized_exts:
                normalized_exts = ["*"]  # Treat ['*'] as the 'all' marker

            # Store source config
            config_sources.append(
                {
                    "root": root,  # Keep relative for now, resolve later
                    "extensions": normalized_exts,
                }
            )

            # Add source-specific excludes to the global excludes list
            # Assume format '*:<pattern>' for excludes defined within a source block
            for pattern in exclude_patterns:
                config_excludes.append(
                    {"extensions": ["*"], "pattern": Path(pattern).as_posix()}
                )

        # --- Parse global output ---
        config_output = config_data.get("output")
        if config_output and not isinstance(config_output, str):
            raise ValueError("Invalid config: 'output' must be a string.")

        # --- Parse global excludes (optional top-level section) ---
        raw_global_excludes = config_data.get("exclude", [])
        if not isinstance(raw_global_excludes, list):
            raise ValueError("Invalid config: Top-level 'exclude' must be an array.")
        for i, ex_table in enumerate(raw_global_excludes):
            if not isinstance(ex_table, dict):
                raise ValueError(
                    f"Invalid config: Item {i} in top-level 'exclude' array is not a table."
                )
            exts = ex_table.get("exts", ["*"])
            pattern = ex_table.get("pattern")
            if pattern is None:
                raise ValueError(
                    f"Invalid config: 'pattern' missing in top-level exclude #{i + 1}"
                )
            if not isinstance(pattern, str):
                raise ValueError(
                    f"Invalid config: 'pattern' must be a string in top-level exclude #{i + 1}"
                )
            if not isinstance(exts, list) or not all(isinstance(e, str) for e in exts):
                raise ValueError(
                    f"Invalid config: 'exts' must be a list of strings in top-level exclude #{i + 1}"
                )

            normalized_exts = [e.lower().lstrip(".") for e in exts]
            if "*" in normalized_exts:
                normalized_exts = ["*"]

            config_excludes.append(
                {"extensions": normalized_exts, "pattern": Path(pattern).as_posix()}
            )

    except tomli.TOMLDecodeError as e:
        raise ValueError(f"Error parsing TOML config file '{config_path}': {e}")
    except FileNotFoundError:
        raise ValueError(f"Config file not found: '{config_path}'")

    return config_sources, config_excludes, config_output


def process_config_and_args(
    include_args: Optional[List[str]],
    exclude_args: Optional[List[str]],
    output_arg: Optional[str],  # Output from CLI args might be None if default used
    config_arg: Optional[str],
) -> Tuple[List[Dict], List[Dict], Path]:
    """
    Loads config, parses CLI args, merges them, and resolves paths.

    Returns:
        Tuple: (final_sources, final_excludes, final_output_path)
               Sources/Excludes contain resolved root paths and normalized patterns/extensions.
    """
    config_sources = []
    config_excludes = []
    config_output = None

    # 1. Load Config File (if provided)
    if config_arg:
        config_path = Path(config_arg)
        if config_path.is_file():
            config_sources, config_excludes, config_output = load_config_from_toml(
                config_path
            )
        else:
            # Argparse should handle file existence, but double-check
            raise ValueError(
                f"Config file path specified but not found or not a file: '{config_arg}'"
            )

    # 2. Parse CLI arguments
    cli_includes = parse_include_exclude_args(include_args)
    cli_excludes = parse_include_exclude_args(exclude_args)
    # Use output_arg directly (it incorporates the argparse default if not provided)
    cli_output = output_arg if output_arg else DEFAULT_OUTPUT_FILENAME

    # 3. Combine sources: CLI overrides config sources entirely if provided.
    final_sources_specs = []
    if cli_includes:
        log.write("[cyan]Using include sources from command line arguments.[/cyan]")
        final_sources_specs = cli_includes  # Use CLI specs directly
    elif config_sources:
        log.write("[cyan]Using include sources from configuration file.[/cyan]")
        final_sources_specs = config_sources  # Use config specs
    else:
        log.write(
            f"[yellow]No includes specified via CLI or config, defaulting to '[bold]{DEFAULT_INCLUDE_SPEC}[/bold]'.[/yellow]"
        )
        final_sources_specs = parse_include_exclude_args([DEFAULT_INCLUDE_SPEC])

    # 4. Combine excludes: CLI appends to config excludes
    # Exclude patterns remain relative path strings for fnmatch
    final_excludes = config_excludes + cli_excludes
    if final_excludes:
        log.write(
            f"Applying [bold yellow]{len(final_excludes)}[/bold yellow] exclusion rule(s)."
        )

    # 5. Determine final output path: CLI > Config > Default
    # cli_output already incorporates the default if needed
    final_output_str = cli_output if cli_output else config_output
    if not final_output_str:  # Should not happen if argparse default is set
        final_output_str = DEFAULT_OUTPUT_FILENAME

    # Resolve output path relative to CWD
    final_output_path = Path(final_output_str).resolve()
    log.write(f"Final output path: [bold green]{final_output_path}[/bold green]")

    # 6. Resolve source roots relative to CWD *after* deciding which specs to use
    resolved_final_sources = []
    for spec in final_sources_specs:
        # spec['pattern'] here is the root directory from include args or config
        resolved_root = Path(spec["pattern"]).resolve()
        resolved_final_sources.append(
            {
                "root": resolved_root,
                "extensions": spec["extensions"],  # Keep normalized extensions
            }
        )

    return resolved_final_sources, final_excludes, final_output_path
