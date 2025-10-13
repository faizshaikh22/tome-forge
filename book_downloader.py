import requests
import os

def download_books(book_map):
    """
    Downloads epub files from Project Gutenberg for a given map of books.

    Args:
        book_map (dict): A dictionary where keys are book names and values are Project Gutenberg book IDs.
    """
    for name, book_id in book_map.items():
        print(f"Downloading {name}...")
        
        # Create the directory for the book
        output_dir = os.path.join("Sources", name)
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
    # Example usage:
    books_to_download = {
        "The Dawn of Day": 39955,
        "Human, All Too Human": 38145,
        "Thus Spoke Zarathustra": 1998,
        "Beyond Good and Evil": 4363,
        "The Antichrist": 19322,
        "The WIll to Power - Book 1-3": 52914,
        "The WIll to Power - Book 3-4": 52915,
        "The Joyful Science": 52881,
        "The Birth of Tragedy": 51356,
        "Ecce Homo": 52190,
        "Twilight of the Idols": 52263,
        "The Genealogy of morals": 52319
    }
    
    download_books(books_to_download)
