"""
Constants and default values for the book generation system.
"""
import os

# Project structure constants
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

# Default configuration values
DEFAULT_BOOK_TITLE = "Untitled Book"
DEFAULT_BOOK_AUTHOR = "Unknown Author"
DEFAULT_OUTPUT_DIR_NAME = "output"
DEFAULT_FILTERS_DIR_NAME = "scripts/filters"  # Relative to project root
DEFAULT_LATEX_TEMPLATE_FILE = "config/latex_template.tex"  # Relative to project root
DEFAULT_MAIN_TEX_FILENAME = "book.tex"
DEFAULT_STATISTICS_FILENAME = "statistics.txt"
DEFAULT_LONGFORM_INDEX_PATH = "Index.md"  # Obsidian addon longform, generates an index
DEFAULT_PDF_FILENAME_TEMPLATE = ""  # If empty, derived from main_tex_filename
DEFAULT_LUA_FILTERS = []
DEFAULT_KEEP_MAIN_TEX = False
DEFAULT_KEEP_LOG_ON_ERROR = True
DEFAULT_KEEP_LOG_ON_SUCCESS = False
DEFAULT_PART_DIVIDER = "Part"

# Standard directory locations
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'config')

# LaTeX/PDF generation constants
WORDS_PER_PAGE = 240  # Average words per page in a typical book