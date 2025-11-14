"""
Service for generating and managing book statistics.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import os
import pandas as pd
from core.chapter import Chapter, ChapterCollection


@dataclass
class StatisticsConfig:
    """Configuration for statistics generation."""
    words_per_page: int = 240
    csv_progress_enabled: bool = True


class StatisticsService:
    """Service for generating and managing book statistics."""
    def __init__(self, config: StatisticsConfig = None):
        self.config = config or StatisticsConfig()

    def generate_statistics(self,
                          collection: ChapterCollection,
                          book_title: str,
                          output_dir: str,
                          statistics_file: str) -> None:
        """
        Generate and save book statistics.

        Args:
            collection: Collection of chapters
            book_title: Title of the book
            output_dir: Directory to save statistics
            statistics_file: Name of the statistics file
        """
        stats = self._calculate_statistics(collection)
        self._write_statistics(stats, book_title, output_dir, statistics_file)
        if self.config.csv_progress_enabled:
            self._update_progress_csv(stats, book_title, output_dir)

    def _calculate_statistics(self, collection: ChapterCollection) -> Dict:
        """Calculate various statistics from the chapter collection."""
        full_chapters = collection.get_full_chapters()

        stats = {
            'total_chapters': len(full_chapters),
            'total_words': collection.total_word_count(),
            'number_of_acts': collection.number_of_acts(),
            'acts_stats': [],
            'total_comments': 0,
            'total_todos': 0
        }

        # Calculate per-act statistics
        for part in range(stats['number_of_acts'] + 1):
            chapters_in_act = collection.get_chapters_by_part(part)
            if not chapters_in_act:
                continue

            act_length = sum(ch.chapter_length for ch in chapters_in_act)
            act_todos = sum(ch.count_todos() for ch in chapters_in_act)
            act_comments = sum(ch.count_comments() for ch in chapters_in_act)

            stats['acts_stats'].append({
                'part': part,
                'num_chapters': len(chapters_in_act),
                'words': act_length,
                'avg_chapter_length': act_length / len(chapters_in_act),
                'todos': act_todos,
                'comments': act_comments
            })

            stats['total_comments'] += act_comments
            stats['total_todos'] += act_todos

        # Calculate additional statistics
        if full_chapters:
            stats['pages'] = stats['total_words'] / self.config.words_per_page
            stats['avg_chapter_length'] = stats['total_words'] / len(full_chapters)

            shortest = collection.get_shortest_chapter()
            longest = collection.get_longest_chapter()
            if shortest:
                stats['shortest_chapter'] = {
                    'number': int(shortest.chapter),
                    'length': shortest.chapter_length
                }
            if longest:
                stats['longest_chapter'] = {
                    'number': int(longest.chapter),
                    'length': longest.chapter_length
                }

        return stats

    def _write_statistics(self,
                         stats: Dict,
                         book_title: str,
                         output_dir: str,
                         statistics_file: str) -> None:
        """Write statistics to a text file."""
        output_path = os.path.join(output_dir, statistics_file)

        with open(output_path, "w") as f:
            def write(*args):
                print(*args, file=f)
                print(*args)  # Also print to console

            write("\n### " + book_title + " Statistics")
            write(f"Total Chapters: {stats['total_chapters']}")
            write(f"Total Words: {stats['total_words']}")
            write(f"Number of acts: {stats['number_of_acts']}")

            for act_stat in stats['acts_stats']:
                write(f"      Part {act_stat['part']} - "
                      f"Chapters: {act_stat['num_chapters']}, "
                      f"Words: {act_stat['words']}")
                write(f"          Average Chapter Length: "
                      f"{act_stat['avg_chapter_length']:.2f} words")

                if act_stat['todos'] > 0:
                    write(f"          TODOs in Part {act_stat['part']}: "
                          f"{act_stat['todos']}")
                if act_stat['comments'] > 0:
                    write(f"          Comments in Part {act_stat['part']}: "
                          f"{act_stat['comments']}")

            if 'pages' in stats:
                write(f"  Approximate (full text) Pages: {stats['pages']:.2f} "
                      f"(based on {self.config.words_per_page} words per page)")
            if 'avg_chapter_length' in stats:
                write(f"Average Chapter Length: {stats['avg_chapter_length']:.2f} words")
            if 'shortest_chapter' in stats:
                write(f"Shortest Chapter: {stats['shortest_chapter']['number']} "
                      f"({stats['shortest_chapter']['length']} words)")
            if 'longest_chapter' in stats:
                write(f"Longest Chapter: {stats['longest_chapter']['number']} "
                      f"({stats['longest_chapter']['length']} words)")

    def _update_progress_csv(self,
                           stats: Dict,
                           book_title: str,
                           output_dir: str) -> None:
        """Update the progress tracking CSV file."""
        safe_name = book_title.replace(" ", "_").replace(":", "")
        progress_file = os.path.join(output_dir, f"{safe_name}_progress.csv")

        progress_data = {
            'Date and time': [pd.Timestamp.now()],
            'Total Chapters': [stats['total_chapters']],
            'Total Words': [stats['total_words']],
            'Pages': [int(stats.get('pages', 0))],
            'Average Chapter Length': [int(stats.get('avg_chapter_length', 0))],
            'Comments': [int(stats['total_comments'])],
            'Todo': [int(stats['total_todos'])]
        }

        # Convert to dataframe
        df = pd.DataFrame(progress_data)

        def save(df_to_save, df_to_concat):
            df_to_save = pd.concat([df_to_concat, df_to_save], ignore_index=True)
            df_to_save.to_csv(progress_file, index=False)
            print(f"Saved progress to: {progress_file}")

        # Append to existing file if it exists
        if os.path.exists(progress_file):
            df_existing = pd.read_csv(progress_file)
            try: #This is horribly ugly lol. Remove try catch and make sure the values in the if are ok manually instead...
                if df_existing["Total Words"].values[-1] != df["Total Words"].values[-1]:
                    save(df, df_existing)
                else:
                    print("Info: Total words unchanged between versions. Skipping updating statistics.")
            except:
                print(f"Warning: Failed to read last row in {progress_file}, appending new value.")
                save()