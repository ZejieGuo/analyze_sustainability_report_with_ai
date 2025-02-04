import os
import json
import argparse
from pinecone import Pinecone
from openai import OpenAI

# Helper function to retrieve environment variables with error handling
def get_env_var(var_name):
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Please set the {var_name} environment variable.")
    return value

openai_api_key = get_env_var("OPENAI_API_KEY")
pc_api_key = get_env_var("PINECONE_API_KEY")

# Initialize Pinecone and OpenAI clients
pc = Pinecone(api_key=pc_api_key)
client = OpenAI(api_key=openai_api_key)


def load_pinecone_api_key() -> str:
    """Load the Pinecone API key from environment variables."""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable is not set.")
    return api_key


def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding

def get_docs(query: str, top_k: int, corporate: str, year: int, index) -> list[str]:
    query_embed = get_embedding(query, model='text-embedding-3-small')
    # search pinecone index
    res = index.query(vector=query_embed, 
                      top_k=top_k, 
                      include_metadata=True,
                      # filter by metadata
                      filter={"corporate": corporate, "year": year}) 

    # extract metadata: text and page number
    docs = [{"text": x["metadata"]['text'], "page_number": x["metadata"].get('page_number', 'N/A')}
            for x in res["matches"]]

    return docs

def extract_and_save_context(tcfd_queries, corporate, year, output_file, index):
    """
    Iterate through a list of queries, retrieve documents, and save the extracted context to a JSON file.
    Append the results to the file if it already exists.

    Parameters:
        tcfd_queries (dict): Dictionary where keys are query names (e.g., "tcfd_01")
                             and values are the corresponding query strings.
        corporate (str): The corporate entity for the retrieval.
        year (int): The year for the retrieval.
        output_file (str): The filename for the output JSON file.
        index: The Pinecone index object.

    Returns:
        None
    """
    # Initialize a dictionary to store all data
    corporate_year_data = {}

    # Key for all contexts combined for a specific corporate and year
    combined_key = f"{corporate}_{year}"
    combined_context = ""

    # Initialize a dictionary for the all_data section
    all_data = {}

    # Iterate through each query in the dictionary
    for query_name, query_text in tcfd_queries.items():
        # Call the get_docs function to retrieve documents for the query
        docs = get_docs(query_text, top_k=20, corporate=corporate, year=year, index=index)
        
        if not docs:
            print(f"No matches found for corporate: {corporate}, year: {year}")
            continue
        
        # Generate the context by joining all retrieved documents
        context = "\n".join(str(doc) for doc in docs)

        # Add the context to the dictionary with the query name as the key
        all_data[query_name] = context

        # Append the context to the combined context
        combined_context += context + "\n"

    # Add the combined context to the all_data dictionary
    all_data[combined_key] = combined_context

    # Wrap the entire data under the corporate_year_data dictionary
    corporate_year_data[combined_key] = all_data

    # Check if the output file already exists
    if os.path.exists(output_file):
        # If file exists, load the existing data
        with open(output_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    else:
        # If file doesn't exist, initialize an empty dictionary
        existing_data = {}

    # Merge the new data with the existing data
    existing_data.update(corporate_year_data)

    # Save the updated data to the JSON file (append operation)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Perform semantic search on Pinecone database and save the output.")
    parser.add_argument("--index_name", type=str, required=True, help="Name of the Pinecone index")
    parser.add_argument("--corporates", type=str, nargs='+', required=True, help="List of corporate names")
    parser.add_argument("--years", type=int, nargs='+', required=True, help="List of years")
    parser.add_argument("--output_file", type=str, required=True, help="Path to the output JSON file")

    args = parser.parse_args()

    # Initialize Pinecone index
    index = pc.Index(args.index_name)

    # Define TCFD queries
    tcfd_queries = {
        "tcfd_01": "How does the company’s board oversee climate-related risks and opportunities?",
        "tcfd_02": "What is the role of management in assessing and managing climate-related risks and opportunities?",
        "tcfd_03": "What are the most relevant climate-related risks and opportunities that the organization has identified over the short, medium, and long term? Are risks clearly associated with a horizon?",
        "tcfd_04": "How do climate-related risks and opportunities impact the organization’s business strategy, economic and financial performance, and financial planning?",
        "tcfd_05": "How resilient is the organization’s strategy when considering different climate-related scenarios, including a 2°C target or lower scenario? How resilient is the organization’s strategy when considering climate physical risks?",
        "tcfd_06": "What processes does the organization use to identify and assess climate-related risks?",
        "tcfd_07": "How does the organization manage climate-related risks?",
        "tcfd_08": "How are the processes for identifying, assessing, and managing climate-related risks integrated into the organization’s overall risk management?",
        "tcfd_09": "What metrics does the organization use to assess climaterelated risks and opportunities? How do these metrics help ensure that performance aligns with its strategy and risk management process?",
        "tcfd_10": "Does the organization disclose its Scope 1, Scope 2, and, if appropriate, Scope 3 greenhouse gas (GHG) emissions? What are the related risks, and do they differ depending on the scope?",
        "tcfd_11": "What targets does the organization use to understand, quantify, and benchmark climate-related risks and opportunities? How is the organization performing against these targets?"
    }

    # Iterate through each corporate and year combination
    for corporate in args.corporates:
        for year in args.years:
            extract_and_save_context(tcfd_queries, corporate, year, args.output_file, index)

if __name__ == "__main__":
    main()