import gutenbergpy.textget
import re
import os

def save_chapters_from_book(book_id, output_dir):
    """
    Downloads a book from Project Gutenberg, cleans it, and saves each chapter.
    It attempts to find the most granular chapters possible.
    """
    print(f"Acquiring text for book ID: {book_id} using 'gutenbergpy'...")
    try:
        raw_text_bytes = gutenbergpy.textget.get_text_by_id(book_id)
        clean_text_bytes = gutenbergpy.textget.strip_headers(raw_text_bytes)
        text = clean_text_bytes.decode('utf-8')
    except Exception as e:
        print(f"Could not process book ID {book_id}. Error: {e}")
        return

    # --- Define Regexes for hierarchical splitting ---
    # More specific pattern for granular chapters (e.g., Chapter 1, CHAPTER I.)
    sub_chapter_pattern = re.compile(r'^\s*(Chapter|CHAPTER)\s+[\dIVXLCDM]+\.?\s*.*?$', re.MULTILINE)
    
    # A more specific, safer pattern for major parts. Looks for keywords or all-caps titles ending in a period.
    major_part_pattern = re.compile(
        r'^\s*(' 
        r'(BOOK|PART|PREFACE|INTRODUCTION|EPILOGUE)\s+[\\dIVXLCDM]+\\.?' # BOOK I, PART 1, etc.
        r'|([A-Z][A-Z\\s,]{4,99}[A-Z]\\.)'                               # OF THE FIRST AND LAST THINGS.
        r')\s*$',
        re.MULTILINE
    )

    # --- Prioritized Splitting Logic ---
    # 1. Try to find granular chapters first.
    matches = list(sub_chapter_pattern.finditer(text))
    if len(matches) > 1:
        print(f"Found {len(matches)} granular chapters (e.g., 'Chapter 1'). Splitting by them.")
        pattern_to_use = sub_chapter_pattern
    else:
        # 2. If not found, fall back to major parts.
        print("No granular chapters found. Falling back to major parts (e.g., 'BOOK I').")
        matches = list(major_part_pattern.finditer(text))
        pattern_to_use = major_part_pattern

    # --- Process the matches ---
    if matches:
        chapter_pairs = []
        for i, match in enumerate(matches):
            title = match.group(0).strip()
            start_pos = match.end()
            # The end position is the start of the next chapter's title
            end_pos = matches[i+1].start() if i + 1 < len(matches) else len(text)
            content = text[start_pos:end_pos]
            chapter_pairs.append((title, content))
        prologue = text[:matches[0].start()]
    else:
        # 3. If no patterns work at all, save the whole book.
        print("Could not split the book into any chapters. Saving full text.")
        book_output_dir = os.path.join(output_dir, f"book_{book_id}_full_text")
        os.makedirs(book_output_dir, exist_ok=True)
        file_path = os.path.join(book_output_dir, f"full_text.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Saved full text to: {file_path}")
        return

    # --- Save the extracted chapters to files ---
    book_output_dir = os.path.join(output_dir, f"book_{book_id}_chapters")
    os.makedirs(book_output_dir, exist_ok=True)
    print(f"Saving chapters to: {book_output_dir}")

    if len(prologue.strip()) > 200:
        file_path = os.path.join(book_output_dir, f"00_prologue.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(prologue.strip())
        print(f"  - Saved: {os.path.basename(file_path)}")

    for i, (title, content) in enumerate(chapter_pairs):
        sanitized_title = re.sub(r'[^\w\s-]', '', title).strip()
        sanitized_title = re.sub(r'[-\s]+', '_', sanitized_title).lower()
        if not sanitized_title:
            sanitized_title = f"chapter_{i+1}"
        
        file_path = os.path.join(book_output_dir, f"{i+1:02d}_{sanitized_title}.txt")
        
        cleaned_content = content.strip()
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(title.strip() + "\n\n")
            f.write(cleaned_content)
        
        print(f"  - Saved: {os.path.basename(file_path)}")

if __name__ == '__main__':
    # --- Book IDs from Project Gutenberg ---
    # 38145: Human, All Too Human
    # 39955: The Dawn of Day
    # 28054: The Brothers Karamazov
    
    # --- Configuration ---
    book_to_process = 28054 # Set to The Brothers Karamazov to test
    output_directory = "D:\\Python projects\\Synthetic data generator\\Extracted Books"

    save_chapters_from_book(book_to_process, output_directory)
