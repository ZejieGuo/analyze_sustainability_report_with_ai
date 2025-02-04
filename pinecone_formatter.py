import json
import re
import argparse
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class PineconeFormatter:
    """A class to format JSON data for Pinecone by extracting metadata from filenames."""

    def __init__(self, input_path: str, output_path: str):
        """Initialize the formatter with input and output file paths."""
        self.input_path = input_path
        self.output_path = output_path
        self.corporate_pattern = re.compile(r"^([A-Za-z]+)")
        self.year_pattern = re.compile(r"_(\d{4})\.pdf$")

    def load_json(self) -> List[Dict]:
        """Load JSON data from the input file."""
        try:
            with open(self.input_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            logging.error(f"Input file not found: {self.input_path}")
            raise
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON format in file: {self.input_path}")
            raise
        except Exception as e:
            logging.error(f"An error occurred while loading the file: {e}")
            raise

    def process_data(self, data: List[Dict]) -> List[Dict]:
        """Process the data to extract corporate names and years from filenames."""
        formatted_data = []
        
        for item in data:
            if not all(key in item for key in ["metadata", "element_id", "embedding", "text"]):
                logging.warning(f"Skipping item due to missing required keys: {item}")
                continue

            file_name = item["metadata"].get("filename", "")
            corporate_match = self.corporate_pattern.match(file_name)
            corporate_name = corporate_match.group(1) if corporate_match else None
            year_match = self.year_pattern.search(file_name)
            year = int(year_match.group(1)) if year_match else None
            
            metadata = {
                "file_name": file_name,
                "text": item["text"],
                "page_number": item["metadata"].get("page_number", 0),
            }
            
            if corporate_name and year:
                metadata["corporate"] = corporate_name
                metadata["year"] = year
            
            formatted_data.append({
                "id": item["element_id"],
                "values": item["embedding"],
                "metadata": metadata,
            })
        
        return formatted_data

    def save_json(self, data: List[Dict]):
        """Save the processed data to the output file."""
        try:
            with open(self.output_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            logging.error(f"An error occurred while saving the file: {e}")
            raise

    def run(self):
        """Run the formatter: load, process, and save data."""
        data = self.load_json()
        processed_data = self.process_data(data)
        self.save_json(processed_data)
        logging.info(f"Processed {len(processed_data)} vectors and saved to {self.output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a JSON file with text chunks and embeddings into Pinecone format, adding corporate name and report year to the metadata.")
    parser.add_argument("--input_file", required=True, help="Path to the input JSON file")
    parser.add_argument("--output_file", required=True, help="Path to the output JSON file in Pinecone data format")
    
    args = parser.parse_args()
    
    formatter = PineconeFormatter(args.input_file, args.output_file)
    formatter.run()