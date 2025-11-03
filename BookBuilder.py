"""
Main script for book generation system.
Handles the orchestration of converting markdown files to a PDF book.
"""
import logging
import sys
from typing import List, Optional
import os

from core import Config, Chapter, ChapterCollection
from services import (
    PandocService, PandocConfig, PandocError,
    LaTeXService, LaTeXConfig, LaTeXError,
    StatisticsService, StatisticsConfig
)
from utils import (
    ensure_directory, clean_directory,
    safe_write_file, get_relative_path
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('book_generation.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class BookGenerator:
    """Main class for orchestrating book generation."""
    
    def __init__(self):
        """Initialize the book generator with its dependencies."""
        self.config = Config()
        self.chapter_collection = ChapterCollection()
        
        # Initialize services
        self.pandoc = PandocService(PandocConfig(
            lua_filters=self.config.build.lua_filters
        ))
        self.latex = LaTeXService(LaTeXConfig(
            keep_main_tex=True,
            keep_log_on_error=True
        ))
        self.stats = StatisticsService(StatisticsConfig(
            words_per_page=240,
            csv_progress_enabled=True
        ))

    def check_dependencies(self) -> bool:
        """Check if all required external tools are available."""
        logger.info("Checking for dependencies...")
        
        if not self.pandoc.is_available():
            logger.error("pandoc not found. Please install pandoc and ensure it's in your PATH.")
            return False
            
        if not self.latex.is_available():
            logger.error("pdflatex not found. Please install a LaTeX distribution and ensure it's in your PATH.")
            return False
            
        logger.info("All dependencies found.")
        return True

    def load_chapters(self) -> None:
        """Load all chapters from the configured directory."""
        logger.info("Loading chapters...")
        current_act = 0
        
        for title in self.config.chapter_titles:
            md_path = os.path.join(self.config.chapters_dir, f"{title}.md")
            
            if self.config.paths.part_divider_key in title:
                current_act += 1
                
            chapter = Chapter(
                chapter=len(self.chapter_collection.chapters) + 1,
                title=title,
                md_path=md_path,
                part=current_act
            )
            self.chapter_collection.add_chapter(chapter)
        
        if not self.chapter_collection.chapters:
            logger.warning(f"No chapter files found in '{self.config.chapters_dir}'")

    def convert_chapters_to_tex(self) -> List[str]:
        """Convert all chapters to LaTeX files."""
        logger.info("\nConverting chapters to LaTeX...")
        converted_files = []
        
        for i, chapter in enumerate(self.chapter_collection.chapters):
            tex_file_name = f"tmp_{i}_{chapter.title.replace(' ', '_')}.tex"
            tex_file_path = os.path.join(self.config.output_dir, tex_file_name)
            
            try:
                self.pandoc.convert_to_latex(
                    chapter.md_path,
                    tex_file_path,
                    self.config.filters_dir
                )
                converted_files.append(tex_file_path)
            except (PandocError, FileNotFoundError) as e:
                logger.error(f"Failed to convert chapter '{chapter.title}': {e}")
                raise
                
        return converted_files

    def generate_main_tex(self, chapter_tex_files: List[str]) -> str:
        """Generate the main LaTeX file that includes all chapters."""
        logger.info("\nGenerating main LaTeX file...")
        main_tex_path = os.path.join(self.config.output_dir, self.config.build.main_tex_filename)
        
        # Replace placeholders in template
        content = self.config.latex_template_content.replace(
            "BOOK_TITLE", self.config.book_details.title
        ).replace(
            "BOOK_AUTHOR", self.config.book_details.author
        ).replace(
            "BOOK_DEDICATION", self.config.book_details.dedication
        )

        # Add chapter includes
        chapters_tex = ""
        if not chapter_tex_files:
            chapters_tex = "% No chapters found or processed.\n\\chapter*{Placeholder Chapter}\n"
            chapters_tex += "Your book content will appear here.\n"
        else:
            for tex_file in chapter_tex_files:
                relative_path = get_relative_path(tex_file, self.config.output_dir).replace("\\", "/")
                chapters_tex += f"\\clearpage\n\\input{{{relative_path}}}\n"

        # Complete the document
        content += chapters_tex + "\n\\end{document}\n"

        try:
            safe_write_file(main_tex_path, content)
            logger.info(f"Main LaTeX file created: {main_tex_path}")
        except IOError as e:
            logger.error(f"Failed to write main LaTeX file: {e}")
            raise

        return main_tex_path

    def compile_and_clean(self, main_tex_path: str) -> bool:
        """Compile the LaTeX file to PDF and clean up."""
        try:
            self.latex.compile_pdf(main_tex_path, self.config.output_dir)
            self.latex.cleanup_files(
                self.config.output_dir,
                self.config.build.main_tex_filename
            )
            logger.info("\nBuild process completed successfully.")
            return True
        except LaTeXError as e:
            logger.error(f"\nBuild process failed during PDF compilation: {e}")
            logger.info(f"Intermediate files kept in '{self.config.output_dir}' for debugging.")
            return False

    def generate_statistics(self) -> None:
        """Generate and save book statistics."""
        try:
            self.stats.generate_statistics(
                self.chapter_collection,
                self.config.book_details.title,
                self.config.output_dir,
                self.config.build.statistics_filename
            )
        except Exception as e:
            logger.error(f"Failed to generate statistics: {e}")
            raise

    def run(self) -> int:
        """
        Run the complete book generation process.
        
        Returns:
            0 for success, 1 for failure
        """
        try:
            if not self.check_dependencies():
                return 1

            # Ensure output directory exists
            ensure_directory(self.config.output_dir)
            logger.info(f"Output directory: '{os.path.abspath(self.config.output_dir)}'")

            # Process chapters
            self.load_chapters()
            converted_files = self.convert_chapters_to_tex()
            
            # Generate and compile main TeX file
            main_tex_path = self.generate_main_tex(converted_files)
            if not self.compile_and_clean(main_tex_path):
                return 1

            # Generate statistics
            self.generate_statistics()
            
            return 0

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            return 1


def main() -> int:
    """Main entry point for the book generation script."""
    generator = BookGenerator()
    return generator.run()


if __name__ == "__main__":
    sys.exit(main())