import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any

def flatten_qa_object(qa_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten nested JSON structure for CSV format"""
    flattened = {
        # Metadata fields
        'author': qa_obj['metadata']['author'],
        'book': qa_obj['metadata']['book'],
        'chapter': qa_obj['metadata']['chapter'],
        'question_id': qa_obj['metadata']['question_id'],
        'layer': qa_obj['metadata']['layer'],
        'llm_provider': qa_obj['metadata']['llm_provider'],
        'llm_model': qa_obj['metadata']['llm_model'],
        
        # Main fields
        'question': qa_obj['question'],
        'answer': qa_obj['answer'],
        
        # Thinking fields
        'thinking_question_analysis': qa_obj['thinking']['question_analysis'],
        'thinking_textual_grounding': qa_obj['thinking'].get('textual_grounding', ''),
        'thinking_reasoning_approach': qa_obj['thinking'].get('reasoning_approach', 
                                                               qa_obj['thinking'].get('reasoningapproach', 
                                                                                     qa_obj['thinking'].get('reasoning approach', ''))),
    }
    
    return flattened

def process_json_file(json_path: Path) -> List[Dict[str, Any]]:
    """Read and process a single JSON file"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Flatten each Q&A object
        return [flatten_qa_object(qa) for qa in data]
    except Exception as e:
        print(f"Error processing {json_path}: {e}")
        return []

def collect_all_jsons(sources_dir: Path) -> List[Dict[str, Any]]:
    """Recursively find and process all JSON files in output folders"""
    all_data = []
    
    # Iterate through each book folder
    for book_dir in sources_dir.iterdir():
        if not book_dir.is_dir():
            continue
            
        output_dir = book_dir / 'output'
        if not output_dir.exists():
            print(f"No output folder found in {book_dir.name}")
            continue
        
        # Process all JSON files in the output folder
        json_files = list(output_dir.glob('*.json'))
        print(f"Processing {len(json_files)} files from {book_dir.name}")
        
        for json_file in json_files:
            data = process_json_file(json_file)
            all_data.extend(data)
    
    return all_data

def write_to_csv(data: List[Dict[str, Any]], output_path: Path):
    """Write flattened data to CSV"""
    if not data:
        print("No data to write!")
        return
    
    fieldnames = [
        'author', 'book', 'chapter', 'question_id', 'layer',
        'llm_provider', 'llm_model', 'question', 'answer',
        'thinking_question_analysis', 'thinking_textual_grounding',
        'thinking_reasoning_approach'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Successfully wrote {len(data)} Q&A pairs to {output_path}")

def main():
    # Get the Sources directory
    sources_dir = Path('Sources')
    
    if not sources_dir.exists():
        print(f"Error: {sources_dir} directory not found!")
        return
    
    # Collect all data
    print("Collecting data from all books...")
    all_data = collect_all_jsons(sources_dir)
    
    # Write to CSV
    output_path = Path('nietzsche.csv')
    write_to_csv(all_data, output_path)
    
    # Print summary
    books = {}
    for item in all_data:
        book = item['book']
        books[book] = books.get(book, 0) + 1
    
    print("\nSummary:")
    for book, count in sorted(books.items()):
        print(f"  {book}: {count} Q&A pairs")
    print(f"\nTotal: {len(all_data)} Q&A pairs")

if __name__ == '__main__':
    main()

