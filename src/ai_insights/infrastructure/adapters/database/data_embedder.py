import os
import json
import glob
import numpy as np
import faiss # Ensure faiss-cpu or faiss-gpu is installed
from datetime import datetime

from src.ai_insights.infrastructure.adapters.llm.ssem_embedder import SSEMEmbedder

# --- Configuration ---
CONFIG = {
    "raw_data_input_dir": "data/raw",  # For community files (e.g., *_brawl.json)
    "processed_data_input_dir": "data/processed",  # For general game data (character_data.json, etc.)
    "rag_index_output_dir": "data/processed/rag_indexes", # Output for FAISS index and metadata
    "games_to_index": ["brawl", "royale"], # Game suffixes for community files
    "community_file_pattern_template": "*_{game_suffix}.json",
    "general_data_files_info": [ # Files from processed_data_input_dir
        {"filename": "character_data.json", "data_type": "character_info"},
        {"filename": "current_meta.json", "data_type": "meta_info"},
        {"filename": "creator_data_all.json", "data_type": "creator_info"}
    ],
    "faiss_index_filename_template": "vector_store_{game_suffix}.faiss",
    "metadata_filename_template": "vector_store_metadata_{game_suffix}.json",
    "max_chunk_length_for_embedding": 1024, # Max chars for text sent to embedding model
    "text_chunk_size_for_splitting": 500, # Target size for text splitting
    "text_chunk_overlap_for_splitting": 50   # Overlap for text splitting
}

def load_json_file(file_path: str) -> any:
    if not os.path.exists(file_path):
        print(f"Info: File not found at {file_path}, skipping.")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content_str = f.read()
            if not content_str.strip():
                print(f"Info: File is empty {file_path}, skipping.")
                return None
            return json.loads(content_str)
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from {file_path}. Error: {e}")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred loading {file_path}: {e}")
        return None


def simple_text_chunker(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Basic chunker. For more advanced, consider LangChain's text_splitters."""
    if not text or not isinstance(text, str):
        return []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
        if start >= len(text): # Ensure last chunk doesn't start beyond text length due to overlap
            break
    return [chunk for chunk in chunks if chunk.strip()]


def extract_text_chunks_and_metadata(json_content: any, source_filename: str, data_type: str, preferred_text_keys: list = None) -> list:
    """
    Extracts text chunks for embedding and associated metadata from JSON content.
    CUSTOMIZE THIS HEAVILY based on your JSON structures.
    Returns: List of tuples: [(text_for_embedding, metadata_dict)]
             metadata_dict must include 'text_chunk_content' and 'data_type'.
    """
    chunks_with_metadata = []
    preferred_text_keys = preferred_text_keys or ["raw_text", "full_text", "text", "content", "summary", "description", "name", "topic", "title"]

    items_to_process = []
    if isinstance(json_content, list):
        items_to_process = json_content # File is a list of items (e.g., characters, community posts)
    elif isinstance(json_content, dict):
        items_to_process = [json_content] # File is a single item/document
    else:
        print(f"Warning: Content from {source_filename} (type: {data_type}) is not a dict or list. Stringifying.")
        text_to_embed = str(json_content)[:CONFIG["max_chunk_length_for_embedding"]]
        if text_to_embed.strip():
            metadata = {
                "source_file": source_filename,
                "data_type": data_type,
                "text_chunk_content": text_to_embed # The string itself is the chunk
            }
            chunks_with_metadata.append((text_to_embed, metadata))
        return chunks_with_metadata

    for item_index, item in enumerate(items_to_process):
        if not isinstance(item, dict):
            # If item in a list is not a dict, treat its string form as a chunk
            text_chunk = str(item)[:CONFIG["max_chunk_length_for_embedding"]]
            if text_chunk.strip():
                metadata = {
                    "source_file": source_filename,
                    "data_type": data_type,
                    "item_index_in_file": item_index if isinstance(json_content, list) else None,
                    "text_chunk_content": text_chunk
                }
                chunks_with_metadata.append((text_chunk, metadata))
            continue

        # Item is a dictionary, try to extract and chunk primary text field
        primary_text_content = None
        document_context_fields = {} # Store other fields for context/metadata

        for key in preferred_text_keys:
            if isinstance(item.get(key), str):
                if key in ["raw_text", "full_text", "text", "content", "details"]: # Keys likely to contain long text
                    primary_text_content = item[key]
                    document_context_fields["original_document_topic"] = item.get("topic", item.get("title", source_filename))
                    break 
                elif primary_text_content is None : # Capture first non-empty preferred key as potential primary text
                    primary_text_content = item[key]
                    document_context_fields["original_document_topic"] = item.get("topic", item.get("title", source_filename))
        
        # Collect other string/numeric fields for a combined text if no single long text field
        other_text_parts = []
        for k, v in item.items():
            if k not in (key for key in preferred_text_keys if item.get(key) == primary_text_content): # Avoid duplicating primary text
                if isinstance(v, str) and v.strip():
                    other_text_parts.append(f"{k}: {v}")
                elif isinstance(v, (int, float, bool)):
                    other_text_parts.append(f"{k}: {str(v)}")
        
        other_fields_text = ". ".join(other_text_parts)

        if primary_text_content and primary_text_content.strip():
            # We found a long text field, chunk it
            text_chunks_from_field = simple_text_chunker(
                primary_text_content,
                CONFIG["text_chunk_size_for_splitting"],
                CONFIG["text_chunk_overlap_for_splitting"]
            )
            for chunk_idx, chunk_str in enumerate(text_chunks_from_field):
                # Text for embedding could be chunk + other contextual fields
                text_for_embedding = f"{document_context_fields.get('original_document_topic', '')}. {other_fields_text}. Chunk: {chunk_str}".strip()
                metadata = {
                    "source_file": source_filename,
                    "data_type": data_type,
                    "item_index_in_file": item_index if isinstance(json_content, list) else None,
                    "chunk_index": chunk_idx,
                    "text_chunk_content": chunk_str, # This is the actual text of the chunk
                    **document_context_fields # Add original_document_topic etc.
                }
                chunks_with_metadata.append((text_for_embedding[:CONFIG["max_chunk_length_for_embedding"]], metadata))
        elif other_fields_text: # No single long text field, use concatenated other fields as one chunk
            text_for_embedding = f"{document_context_fields.get('original_document_topic', '')}. {other_fields_text}".strip()
            metadata = {
                "source_file": source_filename,
                "data_type": data_type,
                "item_index_in_file": item_index if isinstance(json_content, list) else None,
                "text_chunk_content": text_for_embedding, # The concatenated string is the chunk
                 **document_context_fields
            }
            chunks_with_metadata.append((text_for_embedding[:CONFIG["max_chunk_length_for_embedding"]], metadata))
            
    return chunks_with_metadata


def build_index_for_game(game_suffix: str, embedder: SSEMEmbedder):
    print(f"\n--- Building RAG Index for Game Suffix: '{game_suffix}' ---")
    all_texts_for_embedding = []
    all_metadata_for_index = [] # This will store the metadata dicts

    # 1. Process game-specific community files
    community_pattern = os.path.join(CONFIG["raw_data_input_dir"], CONFIG["community_file_pattern_template"].format(game_suffix=game_suffix))
    community_files = glob.glob(community_pattern)
    print(f"Found {len(community_files)} community files for '{game_suffix}' matching '{community_pattern}'")
    for file_path in community_files:
        content = load_json_file(file_path)
        if content:
            # Pass text_keys relevant for community files if they differ
            chunks = extract_text_chunks_and_metadata(content, os.path.basename(file_path), f"community_{game_suffix}")
            for text_to_embed, meta_dict in chunks:
                all_texts_for_embedding.append(text_to_embed)
                all_metadata_for_index.append(meta_dict)

    # 2. Process general data files
    print(f"Processing general data files from '{CONFIG['processed_data_input_dir']}' for game '{game_suffix}' index...")
    for file_info in CONFIG["general_data_files_info"]:
        file_path = os.path.join(CONFIG["processed_data_input_dir"], file_info["filename"])
        content = load_json_file(file_path)
        if content:
            chunks = extract_text_chunks_and_metadata(content, file_info["filename"], file_info["data_type"], file_info.get("text_keys"))
            for text_to_embed, meta_dict in chunks:
                all_texts_for_embedding.append(text_to_embed)
                all_metadata_for_index.append(meta_dict)
    
    if not all_texts_for_embedding:
        print(f"No text content extracted to build index for '{game_suffix}'. Skipping.")
        return

    print(f"Total text chunks to embed for '{game_suffix}': {len(all_texts_for_embedding)}")
    
    embeddings_np = embedder.generate_embeddings(all_texts_for_embedding)
    embeddings_np = np.asarray(embeddings_np, dtype=np.float32)

    if embeddings_np.ndim == 1: # Handle if only one sentence was embedded and model returns 1D array
        embeddings_np = embeddings_np.reshape(1, -1)

    if embeddings_np.size == 0 or embeddings_np.shape[0] != len(all_texts_for_embedding):
        print(f"Error: Embedding generation mismatch or empty for '{game_suffix}'. Expected {len(all_texts_for_embedding)} embeddings, got shape {embeddings_np.shape}. Skipping index creation.")
        return

    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dimension) 
    index.add(embeddings_np)
    print(f"FAISS index built for '{game_suffix}' with {index.ntotal} vectors (dimension: {dimension}).")

    os.makedirs(CONFIG["rag_index_output_dir"], exist_ok=True)
    faiss_path = os.path.join(CONFIG["rag_index_output_dir"], CONFIG["faiss_index_filename_template"].format(game_suffix=game_suffix))
    metadata_path = os.path.join(CONFIG["rag_index_output_dir"], CONFIG["metadata_filename_template"].format(game_suffix=game_suffix))

    faiss.write_index(index, faiss_path)
    print(f"FAISS index for '{game_suffix}' saved to: {faiss_path}")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(all_metadata_for_index, f, indent=2)
    print(f"Metadata for '{game_suffix}' (containing {len(all_metadata_for_index)} items) saved to: {metadata_path}")


if __name__ == "__main__":
    print(f"Data Embedding Script started at {datetime.now().isoformat()}")
    
    # Ensure output directory exists
    os.makedirs(CONFIG["rag_index_output_dir"], exist_ok=True)

    # Check input directories
    if not os.path.isdir(CONFIG["raw_data_input_dir"]):
        print(f"ERROR: Raw data input directory not found: {os.path.abspath(CONFIG['raw_data_input_dir'])}")
    if not os.path.isdir(CONFIG["processed_data_input_dir"]):
        print(f"ERROR: Processed data input directory not found: {os.path.abspath(CONFIG['processed_data_input_dir'])}")

    try:
        print(f"Initializing embedder...")
        ssem_embedder = SSEMEmbedder()
        print("Embedder initialized.")

        for game_key in CONFIG["games_to_index"]:
            build_index_for_game(game_key, ssem_embedder)
        
        print("\nData embedding process finished.")
    except Exception as e:
        print(f"A critical error occurred: {e}")
        import traceback
        traceback.print_exc()
    print(f"Data Embedding Script ended at {datetime.now().isoformat()}")