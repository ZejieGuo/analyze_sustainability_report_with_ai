import json
import argparse
import logging
import os
from typing import List, Dict
import pinecone
from pinecone import Pinecone

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def load_pinecone_api_key() -> str:
    """Load the Pinecone API key from environment variables."""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable is not set.")
    return api_key

def load_json_file(file_path: str) -> List[Dict]:
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in file: {file_path}")
        raise
    except Exception as e:
        logging.error(f"An error occurred while loading the file: {e}")
        raise

def upsert_vectors_in_chunks(index, vectors: List[Dict], chunk_size: int = 300):
    """Upsert vectors into Pinecone index in chunks."""
    for i in range(0, len(vectors), chunk_size):
        chunk = vectors[i:i + chunk_size]
        try:
            index.upsert(vectors=chunk)
            logging.info(f"Upserted chunk {i // chunk_size + 1} of {len(vectors) // chunk_size + 1}")
        except Exception as e:
            logging.error(f"Failed to upsert chunk {i // chunk_size + 1}: {e}")
            raise

def main(input_file: str, index_name: str):
    """Main function to load data, split into chunks, and upsert into Pinecone."""
    # Load Pinecone API key
    api_key = load_pinecone_api_key()
    pc = Pinecone(api_key=api_key)

    # Load the JSON file
    vectors = load_json_file(input_file)
    logging.info(f"Loaded {len(vectors)} vectors from {input_file}")

    # Initialize Pinecone index
    try:
        index = pc.Index(index_name)
    except Exception as e:
        logging.error(f"Failed to initialize Pinecone index: {e}")
        raise

    # Upsert vectors in chunks
    upsert_vectors_in_chunks(index, vectors)

    logging.info("Upsert completed successfully.")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Upsert JSON data into Pinecone index.")
    parser.add_argument("--input_file", required=True, help="Path to the input JSON file")
    parser.add_argument("--index_name", required=True, help="Name of the Pinecone index")
    args = parser.parse_args()

    # Run the main function
    main(args.input_file, args.index_name)