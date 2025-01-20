<!-- Framework -->
<br />
<div align="center">
<h1 align="center">Automatic Sustainability Report Analysis</h3>
  <p align="center">
     A framework for automated corporate sustainability report analysis leveraging semantic chunking and table enrichment techniques to improve table and chart content extraction using foundation LLMs.
  </p>
  <a href="https://github.com/ZejieGuo/analyze_sustainability_report_with_ai">
    <img src="images/pipeline_report_processing.jpeg" alt="Pipeline" width="720">
  </a>
<div align="left">
  <h3 align="left">Report Processing Module</h3>
  <ol align="left">
    <li>Semantic chunking with Unstructured.io</li>
    <li>Marddown table formatting and table enrichment</li>
    <li>Embedding and semantic search with Pinecone DB</li>
  </ol>
  
  <h3 align="left">LLM Agent Module</h3>
  <ol align="left">
    <li>Disclosure information summary with LLMs</li>
    <li>TCFD conformity assessment or Q&A with LLMs based on disclosure sumamries</li>
  </ol>

<div align="left">
  <h2 align="left">Setup</h2>
  
1. **Clone the GitHub Repository**:
```bash
git clone git@github.com:ZejieGuo/analyze_sustainability_report_with_ai.git
```

2. **Set up and Activate Python Environment**

```bash
python -m venv venv_sustain_ai
```

- Now activate this environment:

```bash
source venv_sustain_ai/bin/activate
```

<div align="left">
  <h2 align="left">Report Processing Stage</h2>

1. **Semantic Chunking and Text Extraction**:

```bash
python3 semantic_chunking.py --pdf_dir "./example_sustainability_report/" --output_dir "./example_chunk_output/"
```

2. **Batch File Preparation for GPT API: Markdown Table Transformation and Table Enrichment**:

```bash
python3 context_aware_represensation_batch.py --input_path "./example_chunk_output/" --output_folder "./batch_file/"
```

3. **Batch Processing with GPT API**:

- Upload batch file:

  ```bash
  from openai import OpenAI
  client = OpenAI()

  batch_input_file = client.files.create(
    file=open(f"./batch_file/FILE_NAME.jsonl", "rb"),
    purpose="batch"
  )
  ```

- Creating batch:

  ```bash
  batch_input_file_id = batch_input_file.id

  client.batches.create(
      input_file_id=batch_input_file_id,
      endpoint="/v1/chat/completions",
      completion_window="24h",
      metadata={
        "description": "nightly eval job"
      }
  )
  ```

- Check batch status:
  ```bash
  client.batches.retrieve("BATCH_ID")
  ```
- Check batch output:
  ```bash
  file_response = client.files.content("OUTPUT_FILE_ID")
  print(file_response.text)
  ```
- Save batch output to file:
  ```bash
  with open(f"OUTPUT_FILE_NAME.jsonl", "w", encoding='utf-8') as f:
      f.write(file_response.text)
  ```

4. **Combine Context-Aware Batch Output with Initial Text Chunk File**:

```bash
python3 merge_context_aware_representation.py --batch_output_file "example_context_aware_batch_output/abb_2023_1500char_markdown_description_batch_output.jsonl" --init_text_chunk_file "example_chunk_output/abb_2023_yolox_1500char.json" --output_file "updated_text_chunk/abb_2023_updated.json"
```
