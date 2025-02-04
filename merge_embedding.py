import json
import argparse

def merge_embeddings(jsonl_file_path, json_file_path, output_file_path):
    # Step 1: Read the JSONL file and extract content
    custom_id_to_content = {}
    with open(jsonl_file_path, 'r', encoding='utf-8') as jsonl_file:
        for line in jsonl_file:
            entry = json.loads(line)
            custom_id = entry.get('custom_id')
            content = entry['response']['body']['data'][0]['embedding']
            
            # Store the content using custom_id as the key
            custom_id_to_content[custom_id] = content

    # Step 2: Read the second JSON file, update it, and save
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        elements = json.load(json_file)
        
        for element in elements:
            element_id = element.get('element_id')
            
            # Check if the element_id matches a custom_id from the first file
            if element_id in custom_id_to_content:
                # Add the content as a new key 'embedding'
                element['embedding'] = custom_id_to_content[element_id]

    # Write the updated elements back to the output JSON file
    with open(output_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(elements, json_file, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge embeddings from a JSONL file into a JSON file.")
    parser.add_argument("--input_embedding", required=True, help="Path to the input JSONL file containing embeddings.")
    parser.add_argument("--input_text_chunk", required=True, help="Path to the input JSON file containing context-aware text chunks.")
    parser.add_argument("--output", required=True, help="Path to the output JSON file to save merged data.")
    
    args = parser.parse_args()
    
    merge_embeddings(args.input_embedding, args.input_text_chunk, args.output)