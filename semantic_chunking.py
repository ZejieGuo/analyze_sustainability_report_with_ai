import argparse
import os
import re
from unstructured.staging.base import elements_to_json
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
import nltk

nltk.download('punkt')

def chunk_elements_by_title(elements, max_characters, new_after_n_chars):
    elements = chunk_by_title(elements,
                            combine_text_under_n_chars=max_characters,
                            max_characters=max_characters,
                            new_after_n_chars=new_after_n_chars
                            )
    return elements


# Filter some content 
def filter_elements(elements):
    possible_titles = ["Table of Contents", "Content", "Structure", "Agenda", "List of Figures", "Outline"] # can add more

    # Find the first element that matches any of the possible titles and is categorized as "Title"
    reference_titles = [
        el for el in elements
        if el.text in possible_titles and el.category == "Title"
    ]
    # Get the ID of the matched title element
    reference_ids = [title.id for title in reference_titles]
    elements = [el for el in elements if el.metadata.parent_id not in reference_ids] 
    # Pattern to detect many dots in a row that indicate a Table of Structure. We want to remove this.

    elements = [el for el in elements if not re.search(r'\.{50}', el.text)]
    # Filtering small chunks below 60 chars, as mostly the are not meaningful
    elements = [el for el in elements if el.category != "Header"]
    elements = [el for el in elements if el.category != "Footer"]
    return elements

# Function to process a list of PDFs and save output to a directory
def process_pdfs(pdf_names, output_dir, strategy, infer_table_structure, extract_element_types, languages, hi_res_model_name, max_characters, new_after_n_chars):
    os.makedirs(output_dir, exist_ok=True)

    for pdf_name in pdf_names:
        try:
            file_name = os.path.splitext(os.path.basename(pdf_name))[0]
            output_file = os.path.join(output_dir, f"{file_name}_{hi_res_model_name}_{max_characters}char.json")

            pdf_elements = partition_pdf(
                filename=pdf_name,
                strategy=strategy,
                infer_table_structure=infer_table_structure,
                extract_element_types=extract_element_types,
                languages=languages,
                hi_res_model_name=hi_res_model_name
            )

            pdf_elements = filter_elements(pdf_elements)
            pdf_elements = chunk_elements_by_title(pdf_elements, max_characters, new_after_n_chars)

            elements_to_json(pdf_elements, filename=output_file)
            print(f"Processed and saved: {output_file}")

        except Exception as e:
            print(f"Error processing {pdf_name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Process PDFs and save output in JSON format.")
    parser.add_argument("--pdf_dir", required=True, help="Directory containing PDF files to process.")
    parser.add_argument("--output_dir", required=True, help="Directory to save the processed JSON files.")
    parser.add_argument("--pdf_files", nargs="*", help="Specific PDF files to process (optional). If not provided, all PDFs in the directory will be processed.")
    parser.add_argument("--languages", nargs="*", default=["eng"], help="Languages to use for text extraction. Default is ['eng'].")
    parser.add_argument("--strategy", default="hi_res", help="Strategy for text extraction. Default is 'hi_res'.")
    parser.add_argument("--max_characters", type=int, default=1500, help="Maximum characters per chunk. Default is 1500.")
    parser.add_argument("--new_after_n_chars", type=int, default=1000, help="Soft maximum characters per chunk. Default is 1000.")
    parser.add_argument("--infer_table_structure", type=bool, default=True, help="Whether to infer table structure. Default is True.")
    parser.add_argument("--extract_element_types", nargs="*", default=['Table'], help="Element types to extract. Default is ['Table'].")
    parser.add_argument("--hi_res_model_name", default="yolox", help="Model name for hi_res strategy. Default is 'yolox'.")

    args = parser.parse_args()

    pdf_dir = args.pdf_dir
    output_dir = args.output_dir
    pdf_files = args.pdf_files
    languages = args.languages
    strategy = args.strategy
    max_characters = args.max_characters
    new_after_n_chars = args.new_after_n_chars
    infer_table_structure = args.infer_table_structure
    extract_element_types = args.extract_element_types
    hi_res_model_name = args.hi_res_model_name

    if not pdf_files:
        pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]

    process_pdfs(
        pdf_files, output_dir, strategy, infer_table_structure, extract_element_types,
        languages, hi_res_model_name, max_characters, new_after_n_chars
    )

if __name__ == "__main__":
    main()