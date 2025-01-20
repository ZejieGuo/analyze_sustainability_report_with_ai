
import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in the .env file.")


def create_prompt(html_table: str, table_content_text: str, document_context: str) -> str:
    """Create the prompt for the table description."""
    return f"""You are a helpful assistant tasked with generating a markdown table and its description based on information from a sustainability report. You will be provided with three pieces of information:

    1. An HTML format of a table or chart extracted from a PDF, which may be incomplete or contain missing values
    2. The full table or chart content as a text string, without structure
    3. Context about the table or chart from the original sustainability report

    Your task is to:
    1. Generate a complete markdown table
    2. Provide a detailed description of the markdown table

    Here's how to proceed:

    First, examine the HTML table or chart format:
    {html_table}


    Next, review the full table or chart content:
    {table_content_text}

    Now, based on the given HTML format and text content, first determine whether the content is a chart or a table:
    - If it is a chart, interpret the chart data and convert it into a Markdown table.
    - If it is a table, generate a complete Markdown table by combining the structure from the HTML format with the data from the text content.
    
    Ensure that:
    - All cells are filled with appropriate content
    - The table or chart is properly formatted or interpreted in markdown table
    - Any inconsistencies between the HTML format and text content are resolved logically

    After generating the markdown table, review the context:
    {document_context}

    Using this context and the markdown table you created, generate a detailed description of the table. Your description should:
    - Highlight key data points or trends
    - Provide context for the information presented

    Please provide your output in the following format:

    [Your detailed table description here]

    '''markdown
    [Your generated markdown table here]
    '''
    """

def create_batch_request(element_id: str, prompt: str, max_tokens: int = 1700) -> Dict[str, Any]:
    """Create a single batch request entry."""
    return {
        "custom_id": element_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that formats markdown tables and describes tables."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens
        }
    }

def get_context(elements, current_element):
    """
    Extract context from up to 3 text elements before and after the table element.
    Collects all available text elements if fewer than 3 exist in either direction.
    
    Args:
        elements: List of all elements in the document
        current_element: The table element we're getting context for
        
    Returns:
        str: Combined context text
    """
    # Find the index of the current element
    try:
        current_index = elements.index(current_element)
    except ValueError:
        return ""
    
    context = []
    
    # Get text elements before the table
    before_elements = []
    count = 0
    index = current_index - 1
    while count < 3 and index >= 0:
        element = elements[index]
        if element.get('type') == 'CompositeElement' and 'text' in element:
            before_elements.append(element['text'])
            count += 1
        index -= 1
    
    # Add document metadata if available
    if 'metadata' in current_element and 'filename' in current_element['metadata']:
        context.append(f"Document: {current_element['metadata']['filename']}")
    
    # Add the before elements in correct order (reverse our collection)
    context.extend(reversed(before_elements))
    
    # Get text elements after the table
    count = 0
    index = current_index + 1
    while count < 3 and index < len(elements):
        element = elements[index]
        if element.get('type') == 'CompositeElement' and 'text' in element:
            context.append(element['text'])
            count += 1
        index += 1
    
    return "\n".join(context)

def create_batch_file(input_data: List[Dict], output_file: str, max_tokens: int = 1700) -> None:
    """
    Create a JSONL batch file for processing tables.
    
    Args:
        input_data: List of document elements
        output_file: Path to output JSONL file
    """
    try:
        print(f"Creating batch file: {output_file}")
        batch_requests = []
        table_count = 0
        
        # Process each element
        for element in input_data:
            if element.get('type') == 'Table' and 'metadata' in element:
                try:
                    # Get element ID
                    element_id = element.get('element_id')
                    if not element_id:
                        continue
                    
                    # Get html table format
                    html_table = element['metadata']['text_as_html']

                    table_content_text = element['text']
                    
                    # Get context
                    context = get_context(input_data, element)
                    
                    # Create prompt
                    prompt = create_prompt(html_table, table_content_text, context)
                    
                    # Create batch request
                    batch_request = create_batch_request(element_id, prompt, max_tokens)
                    batch_requests.append(batch_request)
                    table_count += 1
                    
                except Exception as e:
                    print(f"Error processing table {element_id}: {str(e)}")
                    continue
        
        # Write batch requests to JSONL file
        with open(output_file, 'w', encoding='utf-8') as f:
            for request in batch_requests:
                f.write(json.dumps(request, ensure_ascii=False) + '\n')
        
        print(f"Successfully created batch file with {table_count} requests")
        
    except Exception as e:
        print(f"Error creating batch file: {str(e)}")
        raise

def process_file(input_file: str, output_file: str, max_tokens: int = 1700) -> None:
    """Process a single JSON file."""
    try:
        print(f"Processing file: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)

        if not input_data:
            print(f"No data found in {input_file}")
            return

        create_batch_file(input_data, output_file, max_tokens)
    except Exception as e:
        print(f"Error processing file {input_file}: {str(e)}")

def process_folder(input_folder: str, output_folder: str, max_tokens: int = 1700) -> None:
    """Process all JSON files in a folder."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".json"):
            input_file = os.path.join(input_folder, file_name)
            output_file = os.path.join(output_folder, f"{os.path.splitext(file_name)[0]}_markdown_requests.jsonl")
            process_file(input_file, output_file, max_tokens)

def main(input_path: str, output_folder: str, max_tokens: int = 1700) -> None:
    """
    Main function to process a file or folder.
    
    Args:
        input_path: Path to input file or folder
        output_folder: Path to output folder
        max_tokens: Maximum tokens for the API (default: 1700)
    """
    if os.path.isfile(input_path):
        print(f"Processing single file: {input_path}")
        file_name = os.path.basename(input_path).replace('.json', '')
        output_file = os.path.join(output_folder, f"{file_name}_markdown_requests.jsonl")
        process_file(input_path, output_file, max_tokens)
    elif os.path.isdir(input_path):
        print(f"Processing all files in folder: {input_path}")
        process_folder(input_path, output_folder, max_tokens)
    else:
        print(f"Invalid input path: {input_path}. Please provide a valid file or folder.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch processing for table enrichment.")    
    parser.add_argument("--input_path", required=True, help="Input file or folder path (JSON file or folder containing JSON files).")
    parser.add_argument("--output_folder", required=True, help="Output folder for batch files.")
    parser.add_argument("--max_tokens", type=int, default=1700, help="Maximum tokens for GPT (default: 1700).")
    
    args = parser.parse_args()
    main(args.input_path, args.output_folder, args.max_tokens)
