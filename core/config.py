"""
Configuration management for the book generation system.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import os
import yaml
from .constants import (
    DEFAULT_BOOK_TITLE, DEFAULT_BOOK_AUTHOR, DEFAULT_OUTPUT_DIR_NAME,
    DEFAULT_FILTERS_DIR_NAME, DEFAULT_LATEX_TEMPLATE_FILE, DEFAULT_MAIN_TEX_FILENAME,
    DEFAULT_STATISTICS_FILENAME, DEFAULT_LONGFORM_INDEX_PATH, DEFAULT_PDF_FILENAME_TEMPLATE,
    DEFAULT_LUA_FILTERS, DEFAULT_PART_DIVIDER, PROJECT_ROOT, CONFIG_DIR
)


@dataclass
class BookDetails:
    """Book metadata configuration."""
    title: str = DEFAULT_BOOK_TITLE
    author: str = DEFAULT_BOOK_AUTHOR
    dedication: str = ""


@dataclass
class PathConfig:
    """Path configuration settings."""
    output_dir_name: str = DEFAULT_OUTPUT_DIR_NAME
    filters_dir_name: str = DEFAULT_FILTERS_DIR_NAME
    latex_template_file: str = DEFAULT_LATEX_TEMPLATE_FILE
    longform_index_path: str = DEFAULT_LONGFORM_INDEX_PATH
    part_divider_key: str = DEFAULT_PART_DIVIDER


@dataclass
class BuildConfig:
    """Build process configuration."""
    main_tex_filename: str = DEFAULT_MAIN_TEX_FILENAME
    pdf_filename_template: str = DEFAULT_PDF_FILENAME_TEMPLATE
    statistics_filename: str = DEFAULT_STATISTICS_FILENAME
    lua_filters: List[str] = field(default_factory=lambda: DEFAULT_LUA_FILTERS)


class Config:
    """Main configuration class."""
    def __init__(self):
        self.book_details = BookDetails()
        self.paths = PathConfig()
        self.build = BuildConfig()
        self.latex_template_content: str = ""
        self.chapter_titles: List[str] = []
        self._load_config()
        self._load_longform_index()
        self._load_latex_template()

    def _deep_get(self, dictionary: dict, keys: str, default: any = None) -> any:
        """Helper to get nested dictionary values."""
        keys_list = keys.split('.')
        d = dictionary
        for key in keys_list:
            if isinstance(d, dict) and key in d:
                d = d[key]
            else:
                return default
        return d

    def _load_yaml_file(self, filepath: str) -> dict:
        """Load and parse a YAML file."""
        if not os.path.exists(filepath):
            print(f"Warning: File not found: {filepath}")
            return {}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = next(yaml.safe_load_all(f), {})
                return data if isinstance(data, dict) else {}
        except (yaml.YAMLError, IOError) as e:
            print(f"Error reading {filepath}: {e}")
            return {}

    def _load_config(self) -> None:
        """Load main configuration file."""
        config_file_path = os.path.join(CONFIG_DIR, 'config.yml')
        config_data = self._load_yaml_file(config_file_path)

        # Book details
        self.book_details.title = self._deep_get(config_data, 'book_details.title', DEFAULT_BOOK_TITLE)
        self.book_details.author = self._deep_get(config_data, 'book_details.author', DEFAULT_BOOK_AUTHOR)
        self.book_details.dedication = self._deep_get(config_data, 'book_details.dedication', "")

        # Paths
        self.paths.output_dir_name = self._deep_get(config_data, 'paths.output_dir_name', DEFAULT_OUTPUT_DIR_NAME)
        self.paths.filters_dir_name = self._deep_get(config_data, 'paths.filters_dir_name', DEFAULT_FILTERS_DIR_NAME)
        self.paths.latex_template_file = self._deep_get(config_data, 'paths.latex_template_file', DEFAULT_LATEX_TEMPLATE_FILE)
        self.paths.longform_index_path = self._deep_get(config_data, 'paths.longform_index_path', DEFAULT_LONGFORM_INDEX_PATH)
        self.paths.part_divider_key = self._deep_get(config_data, 'paths.part_divider_key', DEFAULT_PART_DIVIDER)

        # Build settings
        self.build.main_tex_filename = self._deep_get(config_data, 'build_settings.main_tex_filename', DEFAULT_MAIN_TEX_FILENAME)
        self.build.pdf_filename_template = self._deep_get(config_data, 'build_settings.pdf_filename_template', DEFAULT_PDF_FILENAME_TEMPLATE)
        self.build.statistics_filename = self._deep_get(config_data, 'build_settings.statistics_filename', DEFAULT_STATISTICS_FILENAME)
        lua_filters = self._deep_get(config_data, 'build_settings.lua_filters', DEFAULT_LUA_FILTERS)
        self.build.lua_filters = lua_filters if isinstance(lua_filters, list) else DEFAULT_LUA_FILTERS

    def _load_longform_index(self) -> None:
        """Load Longform index file and extract chapter titles."""
        def get_titles(potential_scenes: list) -> list:
            """Recursively extract titles from nested scene structure."""
            scenes = []
            for scene in potential_scenes:
                if isinstance(scene, list):
                    scenes.extend(get_titles(scene))
                elif isinstance(scene, str):
                    scenes.append(scene)
            return scenes

        index_data = self._load_yaml_file(self.paths.longform_index_path)
        scenes = index_data.get('longform', {}).get('scenes', [])
        self.chapter_titles = get_titles(scenes)
        self.scene_folder = index_data.get('longform', {}).get('sceneFolder', '')

    def _load_latex_template(self) -> None:
        """Load LaTeX template content."""
        template_path = os.path.join(PROJECT_ROOT, self.paths.latex_template_file)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                self.latex_template_content = f.read()
        except IOError as e:
            print(f"Error reading LaTeX template '{template_path}': {e}")
            self.latex_template_content = ""

    @property
    def output_dir(self) -> str:
        """Get the full path to the output directory."""
        return os.path.join(PROJECT_ROOT, self.paths.output_dir_name)

    @property
    def filters_dir(self) -> str:
        """Get the full path to the filters directory."""
        return os.path.join(PROJECT_ROOT, self.paths.filters_dir_name)

    @property
    def chapters_dir(self) -> str:
        """Get the full path to the chapters directory."""
        return os.path.join(PROJECT_ROOT, os.path.join(
            os.path.dirname(self.paths.longform_index_path),
            self.scene_folder
        ))

    def get_pdf_filename(self) -> str:
        """Get the final PDF filename."""
        if self.build.pdf_filename_template:
            return self.build.pdf_filename_template.format(
                title=self.book_details.title,
                author=self.book_details.author
            )
        return self.build.main_tex_filename.replace(".tex", ".pdf")