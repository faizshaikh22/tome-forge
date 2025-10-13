import os
import re
from bs4 import BeautifulSoup, Tag
from typing import List, Tuple, Optional

def sanitize_filename(name: str) -> str:
    """
    Takes a string and returns a sanitized version suitable for a filename.
    """
    name = re.sub(r'[^\w\s-]', '', name).strip()
    name = re.sub(r'[-\s]+', '_', name)
    name = name.lower()
    return name[:100]

def find_chapters_from_toc(soup: BeautifulSoup) -> List[Tag]:
    """
    Strategy 1: Tries to find chapters by locating a Table of Contents
    and extracting the linked sections. This is the most reliable method.
    """
    print("\n  [TOC Strategy] Searching for Table of Contents heading (e.g., 'Contents')...")    
    # Find a heading tag that contains the text "Contents", even if nested in other tags.
    toc_heading = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3'] and 'Contents' in tag.get_text())

    if not toc_heading:
        print("  [TOC Strategy] -> 'Contents' heading not found.")
        return []
    print(f"  [TOC Strategy] Found TOC heading: '{toc_heading.get_text(strip=True)}'")

    # Find the list (ul) or table (div > table) that contains the TOC links
    toc_container = toc_heading.find_next(['ul', 'div'])
    if not toc_container:
        print("  [TOC Strategy] -> Could not find a 'ul' or 'div' container after the TOC heading.")
        return []
    print(f"  [TOC Strategy] Found potential TOC container: <{toc_container.name}>")
    
    # In some books, the TOC is inside a div containing a table
    if toc_container.name == 'div' and toc_container.find('table'):
        print("  [TOC Strategy] Container is a div with a table, switching to the table.")
        toc_container = toc_container.find('table')
        
    toc_links = toc_container.find_all('a', href=re.compile(r'^#'))
    if not toc_links:
        print(f"  [TOC Strategy] -> Found a container, but it contains no links starting with '#'.")
        return []

    chapter_starts = []
    for link in toc_links:
        chapter_id = link['href'][1:] # Remove the '#'
        
        # Find the element in the document that the TOC links to
        target_element = soup.find(id=chapter_id)
        
        if target_element:
            # The target might be the heading itself or an anchor inside it.
            # We find the closest parent that is a heading tag.
            heading = target_element.find_parent(['h1', 'h2', 'h3', 'h4'])
            if heading and heading not in chapter_starts:
                chapter_starts.append(heading)
            # If the target is the heading itself
            elif target_element.name in ['h1', 'h2', 'h3', 'h4'] and target_element not in chapter_starts:
                 chapter_starts.append(target_element)

    return chapter_starts

def find_chapters_from_headings(soup: BeautifulSoup) -> List[Tag]:
    """
    Strategy 2 (Fallback): Finds chapters by searching for headings (h1, h2, h3)
    that have an 'id' attribute. This works for many books without a standard TOC.
    """
    print("\n  [Heading Scan Strategy] Searching for headings (h1, h2, h3) with 'id' attributes...")
    chapter_starts = []
    for heading_tag in ['h1', 'h2', 'h3']:
        # Find all headings with an 'id'
        headings = soup.find_all(heading_tag)
        print(f"  [Heading Scan Strategy] Found {len(headings)} <{heading_tag}> tags.")
        
        # This regex looks for headings that are likely to be major sections,
        # like "Book I", "Introduction", "Preface", or short, titled sections.
        chapter_pattern = re.compile(r'^(Book|Part|Preface|Introduction|Epilogue|Chapter)\s+[\dIVXLCDM]+|^\s*[A-Z][a-zA-Z\s]{3,50}\.?\s*$', re.IGNORECASE)

        # Filter out boilerplate Project Gutenberg headers/footers and TOC headings
        potential_chapters = [
            h for h in headings
            if not h.find_parent(id='pg-header') and not h.find_parent(id='pg-footer') and chapter_pattern.search(h.get_text(strip=True))
        ]
        print(f"  [Heading Scan Strategy] After filtering PG headers/footers, {len(potential_chapters)} potential chapters remain.")
        
        if len(potential_chapters) > len(chapter_starts):
            print(f"  [Heading Scan Strategy] -> Found a promising set of chapters using <{heading_tag}> tags ({len(potential_chapters)} found).")
            chapter_starts = potential_chapters

    print(f"  [Heading Scan Strategy] -> Final count of chapters found with this strategy: {len(chapter_starts)}")
    return chapter_starts

def extract_chapters_from_html(file_path: str, output_dir: str):
    """
    Extracts chapters from a Project Gutenberg HTML file using multiple strategies.
    It saves chapters as individual text files in the specified output directory.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"Successfully read the file: {file_path}")
    except FileNotFoundError:
        print(f"Error: Input file not found at '{file_path}'")
        return
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return

    soup = BeautifulSoup(content, 'lxml')
    
    # --- Chapter Identification ---
    # Try the most reliable method first (Table of Contents)
    print("Attempting Strategy 1: Find chapters from Table of Contents...")
    chapter_headings = find_chapters_from_toc(soup)
    strategy_used = "Table of Contents"

    # If TOC method fails, use the fallback heading search
    if not chapter_headings:
        print("\nStrategy 1 failed. Attempting Strategy 2: Find chapters from headings...")
        chapter_headings = find_chapters_from_headings(soup)
        strategy_used = "Heading Scan (h1/h2/h3 with id)"
        
    # The standard end-of-book marker
    end_marker = soup.find(id='pg-end-separator')

    if not chapter_headings:
        print("\nCould not find any chapters using any available strategy.")
        print("This book may have a unique format. The script might need further adaptation.")
        return

    print(f"\nFound {len(chapter_headings)} chapters using strategy: '{strategy_used}'. Starting extraction...")
    
    # --- File Output Setup ---
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output will be saved in: {os.path.abspath(output_dir)}")
    except OSError as e:
        print(f"Error creating output directory '{output_dir}': {e}")
        return

    # --- Content Extraction Loop ---
    for i, heading in enumerate(chapter_headings):
        chapter_title = heading.get_text(" ", strip=True)
        print(f"  - Extracting Chapter {i+1}: {chapter_title}")

        content_parts = []
        # Iterate through all tags following the current chapter heading
        for sibling in heading.find_next_siblings():
            # Stop when the next chapter heading or the end-of-book marker is reached
            if sibling in chapter_headings or sibling == end_marker:
                break
            
            # Extract text from the tag
            if isinstance(sibling, Tag):
                # Using a separator adds spaces between inline elements for better readability
                text = sibling.get_text(" ", strip=True)
                if text:
                    content_parts.append(text)

        full_content = '\n\n'.join(content_parts)

        # --- Saving the Chapter to a File ---
        file_title = sanitize_filename(chapter_title)
        filename = f"{i+1:02d}_{file_title}.txt"
        output_file_path = os.path.join(output_dir, filename)

        try:
            with open(output_file_path, 'w', encoding='utf-8') as f_out:
                f_out.write(f"Chapter: {chapter_title}\n\n")
                f_out.write(full_content)
        except IOError as e:
            print(f"    -> Error: Could not write to file {output_file_path}: {e}")

    print("\nExtraction complete.")

def main():
    """
    Main function to define file paths and start the extraction process.
    """
    # === Configuration ===
    # Change this to the path of your downloaded Gutenberg HTML file.
    input_file_path = "D:\\Python projects\\Synthetic data generator\\Sources\\Brothers Karamazov\\pg28054-images.html"
    
    # Change this to your desired output directory name.
    # A new folder with this name will be created.
    output_path = 'extracted_chapters_the_brothers_karamazov'
    
    extract_chapters_from_html(input_file_path, output_path)

if __name__ == '__main__':
    main()