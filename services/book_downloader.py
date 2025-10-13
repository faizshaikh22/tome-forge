import requests
import os
import sys

# Adjust path to import config from the root directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import config

def download_books(book_map):
    """
    Downloads epub files from Project Gutenberg for a given map of books.

    Args:
        book_map (dict): A dictionary where keys are book names and values are Project Gutenberg book IDs.
    """
    # Get the project root directory (the parent of the current script's directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sources_dir = os.path.join(project_root, config.SOURCES_DIR)

    for name, book_id in book_map.items():
        print(f"Downloading {name}...")
        
        # Create the directory for the book
        output_dir = os.path.join(sources_dir, name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Construct the download URL
        url = f"https://www.gutenberg.org/ebooks/{book_id}.epub.images"
        
        # Define the output file path
        output_path = os.path.join(output_dir, "book.epub")
        
        try:
            # Download the book
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Save the book
            with open(output_path, "wb") as f:
                f.write(response.content)
                
            print(f"Successfully downloaded {name} to {output_path}")
            
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {name}: {e}")

if __name__ == "__main__":
    download_books(config.BOOKS_TO_DOWNLOAD)
