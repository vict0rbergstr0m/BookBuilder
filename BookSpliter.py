import argparse
import os
import re
import sys
from pypdf import PdfReader, PdfWriter
from core import Config

def parse_range(value: str):
    """Parses a string like '15' or '10-15' into a start and end tuple."""
    if '-' in value:
        parts = value.split('-')
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ValueError(f"Invalid range format: {value}")
        return int(parts[0]), int(parts[1])
    else:
        if not value.isdigit():
            raise ValueError(f"Invalid number format: {value}")
        return int(value), int(value)

def get_chapter_page_mapping(reader: PdfReader):
    """
    Attempts to map chapter numbers to their 0-indexed starting pages.
    First tries to use PDF outlines/bookmarks. If none exist, falls back to text extraction.
    """
    chapter_starts = {}

    # 1. Try finding chapters via PDF Bookmarks/Outline
    if reader.outline:
        def extract_dests(outline):
            dests = []
            for item in outline:
                if isinstance(item, list):
                    dests.extend(extract_dests(item))
                else:
                    dests.append(item)
            return dests

        for dest in extract_dests(reader.outline):
            if hasattr(dest, 'title') and dest.title:
                # Matches strings like "Chapter 15 - chapter title xxx"
                match = re.search(r'Chapter\s+(\d+)', dest.title, re.IGNORECASE)
                if match:
                    ch_num = int(match.group(1))
                    if ch_num not in chapter_starts:
                        chapter_starts[ch_num] = reader.get_destination_page_number(dest)

    # 2. Fallback: Search text if Outline didn't work
    if not chapter_starts:
        print("No PDF outlines/bookmarks found. Scanning page text for 'Chapter X' (this may take a moment)...")
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                matches = re.finditer(r'Chapter\s+(\d+)', text, re.IGNORECASE)
                for match in matches:
                    ch_num = int(match.group(1))
                    # Only map the FIRST time we see a chapter number
                    if ch_num not in chapter_starts:
                        chapter_starts[ch_num] = i

    return chapter_starts

def main():
    parser = argparse.ArgumentParser(description="Split a generated Book PDF by Chapter or Page.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--chapter', type=str, help="Chapter(s) to keep (e.g., '15' or '10-15')")
    group.add_argument('-p', '--page', type=str, help="Page(s) to keep (e.g., '314' or '120-150')")
    parser.add_argument('-d', '--directory', type=str, help="Optional output directory (defaults to configured output directory)")

    args = parser.parse_args()

    # Initialize Config and locate the PDF
    config = Config()
    pdf_filename = config.get_pdf_filename()
    input_pdf_path = os.path.join(config.output_dir, pdf_filename)
    output_dir = args.directory if args.directory else config.output_dir

    if args.directory:
        os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(input_pdf_path):
        print(f"Error: Could not find PDF at {input_pdf_path}")
        print("Please ensure the book has been built using BookBuilder.py first.")
        sys.exit(1)

    print(f"Reading {input_pdf_path}...")
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)

    start_page_idx = 0
    end_page_idx = 0
    output_suffix = ""

    # --- HANDLE PAGES ---
    if args.page:
        try:
            start_p, end_p = parse_range(args.page)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

        # Convert 1-indexed user input to 0-indexed PyPDF indices
        """
        TODO: since the pdf pages and page number on the page are not the same, consider
        some smart regex to find the first numbered page... Maybe this should be another arg/flag.
        """
        start_page_idx = max(0, start_p - 1)
        end_page_idx = min(total_pages - 1, end_p - 1)
        if start_p == end_p:
            output_suffix = f"Page_{start_p}"
        else:
            output_suffix = f"Pages_{start_p}-{end_p}"

    # --- HANDLE CHAPTERS ---
    elif args.chapter:
        try:
            start_ch, end_ch = parse_range(args.chapter)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

        chapter_mapping = get_chapter_page_mapping(reader)

        if not chapter_mapping:
            print("Error: Could not detect any chapters in the PDF.")
            sys.exit(1)

        available_chapters = sorted(chapter_mapping.keys())

        if start_ch not in available_chapters and start_ch != 0:
            print(f"Error: Chapter {start_ch} not found in document.")
            print(f"Available chapters: {available_chapters}")
            sys.exit(1)

        if start_ch == 0:
            start_page_idx = 0
        else:
            start_page_idx = chapter_mapping[start_ch]

        # Figure out the end page by looking at the start of the chapter *after* end_ch
        if end_ch not in available_chapters:
            # If user asks for 10-15 but it ends at 12, cap it at the last available chapter
            end_ch = available_chapters[-1]
            print(f"Warning: End chapter adjusted to {end_ch} (last chapter in document).")

        end_ch_index_in_list = available_chapters.index(end_ch)

        # If there is a chapter after our target range, stop 1 page before it starts
        if end_ch_index_in_list + 1 < len(available_chapters):
            next_chapter_num = available_chapters[end_ch_index_in_list + 1]
            end_page_idx = chapter_mapping[next_chapter_num] - 1
        else:
            # If it's the last chapter in the book, grab everything until the end of the PDF
            end_page_idx = total_pages - 1

        if start_ch == end_ch:
            output_suffix = f"Chapter_{start_ch}"
        else:
            output_suffix = f"Chapters_{start_ch}-{end_ch}"

    # --- WRITE NEW PDF ---
    writer = PdfWriter()

    # Ensure indices are logical
    if start_page_idx > end_page_idx:
        print("Error: Calculated start page is after end page. Check your range.")
        sys.exit(1)

    print(f"Extracting physical pages {start_page_idx + 1} to {end_page_idx + 1}...")

    for i in range(start_page_idx, end_page_idx + 1):
        writer.add_page(reader.pages[i])

    base_name = os.path.splitext(pdf_filename)[0]
    output_filename = f"{base_name}_{output_suffix}.pdf"
    output_path = os.path.join(output_dir, output_filename)

    with open(output_path, "wb") as output_pdf:
        writer.write(output_pdf)

    print(f"Success! Saved to: {output_path}")

if __name__ == "__main__":
    main()