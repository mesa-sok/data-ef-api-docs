# Semantic Search & Dataset Embeddings

This project includes a high-performance semantic search system that allows you to find Data EF datasets based on their English semantic meaning rather than just exact keywords. It leverages a local embedding model and the Qdrant vector database.

## Overview

The system works by:
1.  **Feature Extraction**: Combining English titles, descriptions, categories, and column schemas into a "Semantic Profile" for each dataset.
2.  **Cleaning**: Strictly removing all Khmer characters to ensure a clean English vector space.
3.  **Embedding**: Generating 768-dimensional vectors using the `embeddinggemma-300m` model.
4.  **Vector Storage**: Persisting these vectors in a local, disk-based Qdrant collection for near-instant retrieval.

## Prerequisites

You must have the `llama-server` running in a Docker container. For high-performance GPUs like the RTX 5090, use the following command to optimize throughput:

```bash
docker run -d --name angry_lichterman --gpus all -p 8081:8080 \
  -v ~/.cache/huggingface/hub/models--unsloth--embeddinggemma-300m-GGUF/embeddinggemma-300M-Q8_0.gguf:/models/embeddinggemma.gguf:ro \
  ghcr.io/ggml-org/llama.cpp:full-cuda \
  --server \
  -m /models/embeddinggemma.gguf \
  --embedding --pooling mean \
  --host 0.0.0.0 --port 8080 \
  --n-gpu-layers -1 \
  --ctx-size 8192 \
  --batch-size 4096 \
  --ubatch-size 1024
```

## Running the Embedding Pipeline

The `embed_datasets.py` script identifies all harvested datasets and builds the Qdrant index. It is idempotent and uses a checkpoint system to resume if interrupted.

```bash
# Process all datasets (805 total)
uv run scripts/search/embed_datasets.py
```

### Configuration
You can override the default batch size or collection name via environment variables:
- `BATCH_SIZE`: Number of items to embed in one request (default: 128).
- `EMBEDDING_API_BASE`: URL of your local llama-server (default: `http://localhost:8081/v1`).
- `COLLECTION_NAME`: The Qdrant collection name (default: `data_ef_datasets`).

## Using Semantic Search

Once the embeddings are stored, you can use the search utility to find relevant datasets:

```bash
uv run scripts/search/search_datasets.py "government financial allocations and budget indicators"
```

### Example Output
```text
Top Semantic Matches:
------------------------------------------------------------
1. [0.5892] Cambodia Budget in Brief FY2025
   ID: pd_6798835848f088000109b0b4
   Category: Public Finance
   Org: General Department of Budget
------------------------------------------------------------
...
```

## Internal Logic

### Feature Selection
The "Semantic Profile" is constructed from:
- Dataset `name`
- Dataset `description`
- Category English names
- Organization English name/abbreviation
- Column technical titles and English descriptions (ignoring `*_kh` columns)

### Storage
Embeddings are stored in the `artifacts/qdrant_storage/` directory. This directory is persistent and should be backed up if you want to avoid re-embedding.
