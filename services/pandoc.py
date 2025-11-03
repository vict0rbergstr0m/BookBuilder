"""
Service for handling Pandoc document conversions.
"""
from dataclasses import dataclass
import subprocess
from typing import List, Optional
import os
import shutil


@dataclass
class PandocConfig:
    """Configuration for Pandoc conversion."""
    markdown_extensions: List[str] = None
    top_level_division: str = "chapter"
    wrap: str = "none"
    highlight_style: Optional[str] = None
    lua_filters: List[str] = None

    def __post_init__(self):
        if self.markdown_extensions is None:
            self.markdown_extensions = ["raw_html"]
        if self.lua_filters is None:
            self.lua_filters = []


class PandocError(Exception):
    """Custom exception for Pandoc-related errors."""
    pass


class PandocService:
    """Service for handling Pandoc document conversions."""
    def __init__(self, config: PandocConfig = None):
        self.config = config or PandocConfig()

    def is_available(self) -> bool:
        """Check if pandoc is available in the system."""
        return bool(shutil.which("pandoc"))

    def build_command(self, input_path: str, output_path: str, filters_dir: str = "") -> List[str]:
        """Build the pandoc command with all necessary arguments."""
        cmd = ["pandoc", input_path]

        # Add markdown format with extensions
        extensions = "+".join(self.config.markdown_extensions)
        cmd.extend(["-f", f"markdown+{extensions}"])

        # Add top-level division setting
        if self.config.top_level_division:
            cmd.extend(["--top-level-division", self.config.top_level_division])

        # Add output format
        cmd.extend(["-t", "latex"])

        # Add wrapping setting
        if self.config.wrap:
            cmd.extend(["--wrap", self.config.wrap])

        # Add syntax highlighting settings
        if self.config.highlight_style is None:
            cmd.append("--no-highlight")
        else:
            cmd.extend(["--highlight-style", self.config.highlight_style])

        # Add LUA filters
        for filter in self.config.lua_filters:
            filter_path = os.path.join(filters_dir, filter)
            if os.path.exists(filter_path):
                cmd.extend(["--lua-filter", filter_path])
            else:
                print(f"Warning: LUA filter not found: {filter_path}")

        # Add output path
        cmd.extend(["-o", output_path])

        return cmd

    def convert_to_latex(self, input_path: str, output_path: str, filters_dir: str = "") -> None:
        """
        Convert a markdown file to LaTeX using pandoc.
        
        Args:
            input_path: Path to input markdown file
            output_path: Path to output LaTeX file
            filters_dir: Directory containing LUA filters
        
        Raises:
            PandocError: If pandoc conversion fails
            FileNotFoundError: If input file doesn't exist
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        cmd = self.build_command(input_path, output_path, filters_dir)

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            print(f"Converted '{os.path.basename(input_path)}' to '{os.path.basename(output_path)}'")
        except subprocess.CalledProcessError as e:
            error_msg = f"Pandoc conversion failed:\nCommand: {' '.join(cmd)}\n"
            if e.stdout:
                error_msg += f"STDOUT:\n{e.stdout}\n"
            if e.stderr:
                error_msg += f"STDERR:\n{e.stderr}"
            raise PandocError(error_msg) from e
        except FileNotFoundError:
            raise PandocError("Pandoc command not found. Is it installed and in your PATH?")