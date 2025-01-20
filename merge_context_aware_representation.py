import json
import argparse

def update_init_chunk(jsonl_file_path, json_file_path, output_file_path):
    """
    Updates a JSON file by incorporating context-aware content from the JSONL batch output file.

    Args:
        jsonl_file_path (str): Path to the batch output file with content to add.
        json_file_path (str): Path to the initial text chunk file to be updated.
        output_file_path (str): Path to save the updated JSON file.
    """
    # Step 1: Read the batch output file and extract content
    custom_id_to_content = {}
    try:
        with open(jsonl_file_path, 'r') as jsonl_file:
            for line in jsonl_file:
                entry = json.loads(line)
                custom_id = entry.get('custom_id')
                content = entry['response']['body']['choices'][0]['message']['content']
                if custom_id:
                    custom_id_to_content[custom_id] = content
    except FileNotFoundError:
        print(f"Error: File {jsonl_file_path} not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSONL file: {e}")
        return

    # Step 2: Read the JSON file, update it, and save
    try:
        with open(json_file_path, 'r') as json_file:
            elements = json.load(json_file)

        updated_count = 0
        for element in elements:
            element_id = element.get('element_id')
            if element_id in custom_id_to_content:
                # Add the content as a new key 'text'
                element['text'] = custom_id_to_content[element_id]
                updated_count += 1

        # Write the updated elements back to the output JSON file
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(elements, json_file, indent=4, ensure_ascii=False)

        print(f"Successfully updated initial text chunk file and saved to {output_file_path}")
        print(f"Number of elements updated: {updated_count}")
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON file: {e}")

def main():
    parser = argparse.ArgumentParser(description="Process and update initial text chunk file with context-aware content from batch output.")
    parser.add_argument("--batch_output_file", required=True, help="Path to the context-aware batch output file.")
    parser.add_argument("--init_text_chunk_file", required=True, help="Path to the initial text chunk file to be updated.")
    parser.add_argument("--output_file", required=True, help="Path to save the updated text chunk file.")
    args = parser.parse_args()

    update_init_chunk(args.batch_output_file, args.init_text_chunk_file, args.output_file)

if __name__ == "__main__":
    main()