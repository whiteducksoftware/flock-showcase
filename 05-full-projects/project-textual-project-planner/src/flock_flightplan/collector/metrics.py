"""
Code quality metrics calculations for the code collector.
Provides functions to analyze code complexity, maintainability and other quality metrics.
"""

import ast
from pathlib import Path
from typing import Dict, Any, List

import radon.metrics as radon_metrics
import radon.raw as radon_raw
from radon.visitors import ComplexityVisitor

from flock_flightplan.cli.utils import print_warning


def calculate_python_metrics(file_path: str) -> Dict[str, Any]:
    """
    Calculate code quality metrics for a Python file.
    
    Args:
        file_path: Path to the Python file
    
    Returns:
        Dictionary containing various code quality metrics
    """
    metrics = {
        "cyclomatic_complexity": None,
        "maintainability_index": None,
        "raw_metrics": None,
        "code_smells": [],
        "complexity_by_function": []
    }
    
    if not file_path.lower().endswith('.py'):
        return metrics
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # Calculate raw metrics (lines of code, comments, etc.)
        raw_metrics = radon_raw.analyze(code)
        metrics["raw_metrics"] = {
            "loc": raw_metrics.loc,  # Lines of code (excluding comments)
            "lloc": raw_metrics.lloc,  # Logical lines of code
            "sloc": raw_metrics.sloc,  # Source lines of code 
            "comments": raw_metrics.comments,  # Number of comments
            "multi": raw_metrics.multi,  # Number of multi-line strings
            "blank": raw_metrics.blank,  # Number of blank lines
            "comment_ratio": raw_metrics.comments / raw_metrics.loc if raw_metrics.loc > 0 else 0
        }
        
        # Calculate maintainability index (0-100, higher is better)
        mi = radon_metrics.mi_visit(code, multi=True)
        metrics["maintainability_index"] = {
            "value": mi,
            "rank": _get_maintainability_rank(mi)
        }
        
        # Calculate cyclomatic complexity
        try:
            # Get complexity for the entire file
            complexity = ComplexityVisitor.from_code(code)
            if complexity.total_complexity is not None:
                # Calculate average complexity manually if needed
                total_complexity = complexity.total_complexity
                num_functions = len(complexity.functions) if complexity.functions else 1
                avg_complexity = total_complexity / num_functions if num_functions > 0 else total_complexity
                
                metrics["cyclomatic_complexity"] = {
                    "total": total_complexity,
                    "average": avg_complexity,
                    "rank": _get_complexity_rank(avg_complexity)
                }
            
            # Get complexity for each function/method
            for item in complexity.functions:
                metrics["complexity_by_function"].append({
                    "name": item.name,
                    "line_number": item.lineno,
                    "complexity": item.complexity,
                    "rank": _get_complexity_rank(item.complexity)
                })
                
                # Identify code smells based on complexity
                if item.complexity > 10:
                    metrics["code_smells"].append({
                        "type": "high_complexity",
                        "location": f"{item.name} (line {item.lineno})",
                        "description": f"Function has high cyclomatic complexity ({item.complexity})",
                        "suggestion": "Consider refactoring into smaller functions"
                    })
        except SyntaxError:
            # Fall back to simpler analysis if visitor fails
            pass
        
        # Check for additional code smells
        metrics["code_smells"].extend(_detect_code_smells(code, file_path))
        
    except Exception as e:
        print_warning(f"Could not analyze metrics in {file_path}: {str(e)}")
    
    return metrics


def _get_complexity_rank(complexity: float) -> str:
    """
    Convert a cyclomatic complexity score to a letter rank.
    
    Args:
        complexity: The cyclomatic complexity value
    
    Returns:
        Letter rank from A (best) to F (worst)
    """
    if complexity <= 5:
        return "A"  # Low - good
    elif complexity <= 10:
        return "B"  # Medium - acceptable
    elif complexity <= 20:
        return "C"  # High - concerning
    elif complexity <= 30:
        return "D"  # Very high - problematic
    else:
        return "F"  # Extremely high - needs immediate refactoring


def _get_maintainability_rank(mi_value: float) -> str:
    """
    Convert a maintainability index to a letter rank.
    
    Args:
        mi_value: The maintainability index value
    
    Returns:
        Letter rank from A (best) to F (worst)
    """
    if mi_value >= 85:
        return "A"  # Highly maintainable
    elif mi_value >= 65:
        return "B"  # Maintainable
    elif mi_value >= 40:
        return "C"  # Moderately maintainable
    elif mi_value >= 25:
        return "D"  # Difficult to maintain
    else:
        return "F"  # Very difficult to maintain


def _detect_code_smells(code: str, file_path: str) -> List[Dict[str, str]]:
    """
    Detect common code smells in Python code.
    
    Args:
        code: Python code as a string
        file_path: Path to the Python file (for reporting)
    
    Returns:
        List of detected code smells with descriptions
    """
    smells = []
    
    try:
        tree = ast.parse(code)
        
        # Check for long functions (by line count)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if func_lines > 50:
                    smells.append({
                        "type": "long_function",
                        "location": f"{node.name} (line {node.lineno})",
                        "description": f"Function is too long ({func_lines} lines)",
                        "suggestion": "Consider breaking into smaller functions"
                    })
                
                # Check for too many parameters
                if len(node.args.args) > 7:  # Including self for methods
                    smells.append({
                        "type": "too_many_parameters",
                        "location": f"{node.name} (line {node.lineno})",
                        "description": f"Function has too many parameters ({len(node.args.args)})",
                        "suggestion": "Consider using a class or data objects to group parameters"
                    })
                    
        # Check for too many imports (module level)
        import_count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_count += len(node.names)
        
        if import_count > 15:
            smells.append({
                "type": "too_many_imports",
                "location": f"{Path(file_path).name}",
                "description": f"Module has too many imports ({import_count})",
                "suggestion": "Consider refactoring to reduce dependencies"
            })
            
    except Exception:
        # Silently fail for syntax errors or other parsing issues
        pass
    
    return smells


def calculate_file_metrics(file_path: str) -> Dict[str, Any]:
    """
    Calculate appropriate metrics based on file type.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Dictionary of metrics appropriate for the file type
    """
    metrics = {}
    
    # Handle Python files
    if file_path.lower().endswith('.py'):
        metrics = calculate_python_metrics(file_path)
    
    # TODO: Add support for other languages (JavaScript, etc.)
    # elif file_path.lower().endswith('.js'):
    #     metrics = calculate_javascript_metrics(file_path)
    
    return metrics 