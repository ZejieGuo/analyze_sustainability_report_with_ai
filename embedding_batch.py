import os
import json
import argparse
from typing import List, Dict, Any

def create_batch_request(element_id: str, text_content: str) -> Dict[str, Any]:
    """Create a single batch request entry."""
    return {
        "custom_id": element_id,
        "method": "POST",
        "url": "/v1/embeddings",
        "body": {
            "model": "text-embedding-3-small",
            "input": text_content,
            "encoding_format": "float"
        }
    }

def create_batch_file(input_data: List[Dict], output_file: str) -> None:
    try:
        print(f"Creating batch file: {output_file}")
        batch_requests = []
        
        # Process each element
        for element in input_data:
            element_id = element.get('element_id')
            text_content = element.get('text')
            
            # Validate inputs
            if element_id is None or text_content is None:
                print(f"Skipping element due to missing data: {element}")
                continue
            
            # Create batch request
            batch_request = create_batch_request(element_id, text_content)
            batch_requests.append(batch_request)

        # Write batch requests to JSONL file
        with open(output_file, 'w', encoding='utf-8') as f:
            for request in batch_requests:
                f.write(json.dumps(request, ensure_ascii=False) + '\n')
                
    except Exception as e:
        print(f"Error creating batch file: {str(e)}")
        raise

def process_folder(input_folder: str, output_folder: str) -> None:
    """Process all JSON files in a folder."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".json"):
            input_file = os.path.join(input_folder, file_name)
            output_file = os.path.join(output_folder, f"{os.path.splitext(file_name)[0]}_embedding_requests.jsonl")
            main(input_file, output_file)

def main(input_path: str, output_folder: str) -> None:
    """
    Main function to process a file or folder.
    
    Args:
        input_path: Path to input file or folder
        output_folder: Path to output folder
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if os.path.isfile(input_path):
        print(f"Processing single file: {input_path}")
        file_name = os.path.basename(input_path).replace('.json', '')
        output_file = os.path.join(output_folder, f"{file_name}_embedding_requests.jsonl")
        create_batch_file(json.load(open(input_path, 'r', encoding='utf-8')), output_file)
    elif os.path.isdir(input_path):
        print(f"Processing all files in folder: {input_path}")
        process_folder(input_path, output_folder)
    else:
        print(f"Invalid input path: {input_path}. Please provide a valid file or folder.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate batch embedding requests for the updated context-aware text chunks.")
    parser.add_argument("--input_path", required=True, help="Input file or folder path (JSON file or folder containing JSON files).")
    parser.add_argument("--output_folder", required=True, help="Output folder for batch files.")
    
    args = parser.parse_args()
    main(args.input_path, args.output_folder)    