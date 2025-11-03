"""
Path handling utilities for the book generation system.
"""
import os
from typing import List, Optional, Tuple


def normalize_path(path: str) -> str:
    """
    Normalize a path to use the correct separators for the current OS.
    
    Args:
        path: Path to normalize
        
    Returns:
        Normalized path as a string
    """
    return os.path.normpath(path)


def ensure_absolute_path(path: str, base_dir: Optional[str] = None) -> str:
    """
    Ensure a path is absolute, converting it if it's relative.
    
    Args:
        path: Path to check/convert
        base_dir: Base directory for relative paths
        
    Returns:
        Absolute path as a string
    """
    if os.path.isabs(path):
        return path
    if base_dir is None:
        base_dir = os.getcwd()
    return os.path.abspath(os.path.join(base_dir, path))


def get_project_root(start_path: str = None) -> str:
    """
    Find the project root directory by looking for common project files.
    
    Args:
        start_path: Path to start searching from (default: current directory)
        
    Returns:
        Absolute path to project root
        
    Raises:
        FileNotFoundError: If project root cannot be determined
    """
    if start_path is None:
        start_path = os.getcwd()

    markers = ['config.yml', '.git', 'pyproject.toml', 'setup.py']
    
    current = os.path.abspath(start_path)
    while True:
        if any(os.path.exists(os.path.join(current, marker)) for marker in markers):
            return current
        
        parent = os.path.dirname(current)
        if parent == current:  # Reached root directory
            raise FileNotFoundError("Could not determine project root")
        current = parent


def split_path(path: str) -> Tuple[str, str, str]:
    """
    Split a path into directory, filename, and extension.
    
    Args:
        path: Path to split
        
    Returns:
        Tuple of (directory, filename, extension)
    """
    directory = os.path.dirname(path)
    filename = os.path.basename(path)
    name, ext = os.path.splitext(filename)
    return directory, name, ext


def find_files(directory: str,
               patterns: List[str],
               recursive: bool = True) -> List[str]:
    """
    Find files matching patterns in a directory.
    
    Args:
        directory: Directory to search
        patterns: List of glob patterns to match
        recursive: Whether to search subdirectories
        
    Returns:
        List of matching file paths
    """
    import glob

    matches = []
    for pattern in patterns:
        if recursive:
            search_pattern = os.path.join(directory, '**', pattern)
            matches.extend(glob.glob(search_pattern, recursive=True))
        else:
            search_pattern = os.path.join(directory, pattern)
            matches.extend(glob.glob(search_pattern))
    
    return sorted(set(matches))  # Remove duplicates and sort


def is_subpath(path: str, parent: str) -> bool:
    """
    Check if a path is a subpath of another directory.
    
    Args:
        path: Path to check
        parent: Potential parent directory
        
    Returns:
        True if path is a subpath of parent, False otherwise
    """
    path = os.path.abspath(path)
    parent = os.path.abspath(parent)
    
    try:
        os.path.relpath(path, parent)
        return True
    except ValueError:
        return False