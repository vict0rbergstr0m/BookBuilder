"""
File operation utilities for the book generation system.
"""
import os
import shutil
import glob
from typing import List, Optional


def ensure_directory(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
    """
    os.makedirs(directory, exist_ok=True)


def clean_directory(directory: str,
                   patterns: List[str],
                   exclude: Optional[List[str]] = None) -> None:
    """
    Clean up files in a directory matching certain patterns.
    
    Args:
        directory: Directory to clean
        patterns: List of glob patterns to match files to delete
        exclude: Optional list of filenames to preserve
    """
    exclude = exclude or []
    for pattern in patterns:
        for filepath in glob.glob(os.path.join(directory, pattern)):
            if os.path.basename(filepath) not in exclude:
                try:
                    os.remove(filepath)
                except OSError as e:
                    print(f"Error deleting '{filepath}': {e}")


def safe_read_file(filepath: str, encoding: str = 'utf-8') -> str:
    """
    Safely read a file's contents.
    
    Args:
        filepath: Path to the file
        encoding: File encoding (default: utf-8)
    
    Returns:
        The file's contents as a string
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with a different encoding if UTF-8 fails
        with open(filepath, 'r', encoding='latin-1') as f:
            return f.read()


def safe_write_file(filepath: str,
                   content: str,
                   encoding: str = 'utf-8',
                   create_dirs: bool = True) -> None:
    """
    Safely write content to a file.
    
    Args:
        filepath: Path to the file
        content: Content to write
        encoding: File encoding (default: utf-8)
        create_dirs: Whether to create parent directories if they don't exist
        
    Raises:
        IOError: If there's an error writing the file
    """
    if create_dirs:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    try:
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
    except IOError as e:
        raise IOError(f"Error writing to '{filepath}': {e}")


def copy_with_backup(src: str, dst: str, backup_suffix: str = '.bak') -> None:
    """
    Copy a file while creating a backup of the destination if it exists.
    
    Args:
        src: Source file path
        dst: Destination file path
        backup_suffix: Suffix for backup files
    """
    if os.path.exists(dst):
        backup = dst + backup_suffix
        try:
            shutil.copy2(dst, backup)
        except OSError as e:
            print(f"Warning: Could not create backup of '{dst}': {e}")
    
    shutil.copy2(src, dst)


def get_relative_path(path: str, base: str) -> str:
    """
    Get a path relative to a base directory.
    
    Args:
        path: Path to convert
        base: Base directory
        
    Returns:
        Relative path as a string
    """
    return os.path.relpath(path, base)