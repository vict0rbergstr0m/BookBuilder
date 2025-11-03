"""
Chapter class and related functionality for managing book chapters.
"""
from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class Chapter:
    """Represents a chapter in the book."""
    chapter: float
    title: str
    md_path: str
    part: int = 0
    _text: Optional[str] = None
    _word_count: Optional[int] = None

    @property
    def text(self) -> str:
        """Lazy load and return the chapter text."""
        if self._text is None:
            self._text = self._load_text()
        return self._text

    @property
    def chapter_length(self) -> int:
        """Return the word count of the chapter."""
        if self._word_count is None:
            self._word_count = len(self.text.split())
        return self._word_count

    def _load_text(self) -> str:
        """Load the chapter text from file."""
        if not os.path.exists(self.md_path):
            return ""
        try:
            with open(self.md_path, "r", encoding="utf-8") as f:
                return f.read()
        except IOError as e:
            print(f"Error reading chapter file '{self.md_path}': {e}")
            return ""

    def is_full_chapter(self) -> bool:
        """Check if this is a full chapter (not a fragment or placeholder)."""
        return self.chapter == round(self.chapter) and self.chapter_length > 250

    def count_todos(self) -> int:
        """Count the number of TODO items in the chapter."""
        import re
        return len(re.findall(r'\bTODO\b', self.text, re.IGNORECASE))

    def count_comments(self) -> int:
        """Count the number of comments in the chapter."""
        import re
        return len(re.findall(r'%%', self.text, re.MULTILINE))


class ChapterCollection:
    """Manages a collection of chapters."""
    def __init__(self):
        self.chapters: list[Chapter] = []

    def add_chapter(self, chapter: Chapter) -> None:
        """Add a chapter to the collection."""
        self.chapters.append(chapter)

    def get_full_chapters(self) -> list[Chapter]:
        """Return only the full chapters (not fragments or placeholders)."""
        return [ch for ch in self.chapters if ch.is_full_chapter()]

    def get_chapters_by_part(self, part: int) -> list[Chapter]:
        """Return all chapters in a specific part/act."""
        return [ch for ch in self.chapters if ch.part == part]

    def total_word_count(self) -> int:
        """Return total word count across all chapters."""
        return sum(ch.chapter_length for ch in self.chapters)

    def number_of_acts(self) -> int:
        """Return the total number of acts/parts in the book."""
        if not self.chapters:
            return 0
        return int(max(ch.part for ch in self.chapters))

    def get_shortest_chapter(self) -> Optional[Chapter]:
        """Return the shortest chapter by word count."""
        full_chapters = self.get_full_chapters()
        return min(full_chapters, key=lambda c: c.chapter_length) if full_chapters else None

    def get_longest_chapter(self) -> Optional[Chapter]:
        """Return the longest chapter by word count."""
        full_chapters = self.get_full_chapters()
        return max(full_chapters, key=lambda c: c.chapter_length) if full_chapters else None