"""
Service for generating and managing book statistics.
"""
from dataclasses import dataclass
import math
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
    def __init__(self, config: Optional[StatisticsConfig] = None):
        self.config = config or StatisticsConfig()

    def generate_statistics(self,
                          collection: ChapterCollection,
                          book_title: str,
                          output_dir: str,
                          target_word_count: int,
                          start_date: str,
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
        if self.config.csv_progress_enabled:
            progress_data = self._update_progress_csv(stats, book_title, output_dir)
            self._add_progress_statistics(stats, progress_data)
            self._save_derived_progress_statistics(progress_data, stats, book_title, output_dir)
        else:
            self._add_progress_statistics(stats, None)
        self._write_statistics(stats, book_title, output_dir, target_word_count, start_date, statistics_file)

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

    def _add_progress_statistics(self,
                               stats: Dict,
                               progress_data: Optional[pd.DataFrame]) -> None:
        """Add analysis that can be derived from the progress CSV."""
        total_average = 0
        average_30_days = 0
        words_since_update = 0
        words_last_7_days = 0
        words_last_30_days = 0
        words_added_on_active_days = 0
        active_writing_days = 0
        longest_gap = 0
        comments_trend = 0

        if progress_data is not None and not progress_data.empty:
            progress_data = progress_data.copy()
            progress_data['Date and time'] = pd.to_datetime(
                progress_data['Date and time'], format='mixed', errors='coerce'
            )
            progress_data['Total Words'] = pd.to_numeric(
                progress_data['Total Words'], errors='coerce'
            )
            progress_data['Comments'] = pd.to_numeric(
                progress_data['Comments'], errors='coerce'
            )
            progress_data = progress_data.dropna(subset=['Date and time', 'Total Words'])
            progress_data = progress_data.sort_values('Date and time')

            if len(progress_data) > 1:
                first = progress_data.iloc[0]
                last = progress_data.iloc[-1]
                previous = progress_data.iloc[-2]
                words_since_update = last['Total Words'] - previous['Total Words']
                total_days = (last['Date and time'] - first['Date and time']).total_seconds() / 86400
                if total_days > 0:
                    total_average = (last['Total Words'] - first['Total Words']) / total_days

                cutoff = last['Date and time'] - pd.Timedelta(days=30)
                older_rows = progress_data[progress_data['Date and time'] <= cutoff]
                first_30_days = older_rows.iloc[-1] if not older_rows.empty else first
                cutoff_7 = last['Date and time'] - pd.Timedelta(days=7)
                older_rows_7 = progress_data[progress_data['Date and time'] <= cutoff_7]
                first_7_days = older_rows_7.iloc[-1] if not older_rows_7.empty else first
                words_last_7_days = last['Total Words'] - first_7_days['Total Words']
                words_last_30_days = last['Total Words'] - first_30_days['Total Words']
                days_30 = (last['Date and time'] - first_30_days['Date and time']).total_seconds() / 86400
                if days_30 > 0:
                    average_30_days = (last['Total Words'] - first_30_days['Total Words']) / days_30

                progress_data['Calendar day'] = progress_data['Date and time'].dt.date
                daily_words = progress_data.groupby('Calendar day')['Total Words'].last()
                daily_additions = daily_words.diff().fillna(daily_words.iloc[0])
                active_additions = daily_additions[daily_additions > 0]
                active_writing_days = len(active_additions)
                words_added_on_active_days = active_additions.sum()

                gaps = progress_data['Date and time'].diff().dt.total_seconds() / 86400
                longest_gap = gaps.max() if not gaps.empty else 0

                if 'Comments' in progress_data and not progress_data['Comments'].isna().all():
                    comments_start = (older_rows['Comments'].dropna()
                                      if not older_rows.empty
                                      else progress_data['Comments'].dropna())
                    comments_end = progress_data['Comments'].dropna()
                    if not comments_start.empty and not comments_end.empty:
                        comments_trend = comments_end.iloc[-1] - comments_start.iloc[-1]

        stats['average_words_per_day'] = total_average
        stats['average_words_per_day_30'] = average_30_days
        stats['words_since_update'] = words_since_update
        stats['words_last_7_days'] = words_last_7_days
        stats['words_last_30_days'] = words_last_30_days
        stats['words_added_on_active_days'] = words_added_on_active_days
        stats['active_writing_days'] = active_writing_days
        stats['average_words_per_active_day'] = (
            words_added_on_active_days / active_writing_days
            if active_writing_days else 0
        )
        stats['longest_gap_days'] = longest_gap
        stats['comments_trend'] = comments_trend

    def _save_derived_progress_statistics(self,
                                         progress_data: pd.DataFrame,
                                         stats: Dict,
                                         book_title: str,
                                         output_dir: str) -> None:
        """Store the latest CSV-derived analysis alongside the snapshot."""
        safe_name = book_title.replace(" ", "_").replace(":", "")
        progress_file = os.path.join(output_dir, f"{safe_name}_progress.csv")
        derived_data = {
            'Words Added Since Last Update': stats['words_since_update'],
            'Words Added Last 7 Days': stats['words_last_7_days'],
            'Words Added Last 30 Days': stats['words_last_30_days'],
            'Lifetime Average Words Per Calendar Day': stats['average_words_per_day'],
            '30 Day Average Words Per Calendar Day': stats['average_words_per_day_30'],
            'Average Words Per Active Writing Day': stats['average_words_per_active_day'],
            'Active Writing Days': stats['active_writing_days'],
            'Longest Gap Between Updates (Days)': stats['longest_gap_days'],
            'Comments Trend (30 Days)': stats['comments_trend']
        }
        for column, value in derived_data.items():
            progress_data.loc[progress_data.index[-1], column] = value
        progress_data.to_csv(progress_file, index=False)

    def _write_statistics(self,
                         stats: Dict,
                         book_title: str,
                         output_dir: str,
                         target_word_count: int,
                         start_date: str,
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
            write(f"Target words {target_word_count}")
            write(f"Words added since last update {stats['words_since_update']:+g}")
            write(f"Words added last 7 days {stats['words_last_7_days']:+g}")
            write(f"Words added last 30 days {stats['words_last_30_days']:+g}")
            write(f"Lifetime average words per calendar day {int(stats['average_words_per_day'])}")
            write(f"30-day average words per calendar day {int(stats['average_words_per_day_30'])}")
            write(f"Average words per active writing day {stats['average_words_per_active_day']:.2f}")
            write(f"Active writing days {stats['active_writing_days']}")
            write(f"Longest gap between updates {stats['longest_gap_days']:.2f} days")
            write(f"Comments trend (30 days) {stats['comments_trend']:+g}")

            words_left = target_word_count - stats['total_words']
            efficiency_factor = 0.75
            total_average = stats['average_words_per_day']
            average_30_days = stats['average_words_per_day_30']
            average_chapter_length = stats.get('avg_chapter_length', 0)
            if average_chapter_length > 0:
                chapters_left = math.ceil(words_left / average_chapter_length)
                write(f"Chapters left {chapters_left}")
                estimated_total_chapters = stats['total_chapters'] + chapters_left
                write(f"Estimated total chapters {estimated_total_chapters}")
            if total_average > 0:
                days_left = words_left / total_average / efficiency_factor
                finish_date = pd.Timestamp.now() + pd.Timedelta(days=days_left)
                write(f"Words left {words_left}")
                write(f"Days left (total average) {int(days_left)}")
                write(f"Est. completion date {finish_date.strftime('%d %B %Y')}")
            if average_30_days > 0:
                days_left_30 = words_left / average_30_days / efficiency_factor
                write(f"Days left (30-day average) {int(days_left_30)}")

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
                           output_dir: str) -> pd.DataFrame:
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
            df_to_save = df_to_save.dropna(how='all')
            df_to_save.to_csv(progress_file, index=False)
            print(f"Saved progress to: {progress_file}")
            return df_to_save

        # Append to existing file if it exists
        if os.path.exists(progress_file):
            try:
                df_existing = pd.read_csv(progress_file).dropna(how='all')
                if (not df_existing.empty and "Total Words" in df_existing and
                        df_existing["Total Words"].iloc[-1] == df["Total Words"].iloc[-1]):
                    print("Info: Total words unchanged between versions. Skipping updating statistics.")
                    return df_existing
                return save(df, df_existing)
            except (OSError, pd.errors.ParserError, KeyError, IndexError):
                print(f"Warning: Failed to read last row in {progress_file}, appending new value.")
                return save(df, pd.DataFrame())

        return save(df, pd.DataFrame())