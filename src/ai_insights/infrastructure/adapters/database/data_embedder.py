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
    "metadata_filename_template": "vector_store_metadata_{game_suffix}.json"
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

def extract_text_chunks_and_metadata(json_content: any, source_filename: str, data_type: str) -> list:
    chunks_with_metadata = []
    # Default: treat the whole JSON content as one document if it's a dictionary
    if isinstance(json_content, dict):
        text_parts = [str(v) for k, v in json_content.items() if isinstance(v, (str, int, float, bool))]
        text_to_embed = ". ".join(text_parts).strip()
        
        if text_to_embed:
            metadata = {"source_file": source_filename, "data_type": data_type, "original_content": json_content}
            chunks_with_metadata.append((text_to_embed[:1024], metadata)) # Truncate for embedding model
    else:
        print(f"Warning: Content from {source_filename} is not a dict ({type(json_content)}), attempting to stringify.")
        text_to_embed = str(json_content)[:1024]
        if text_to_embed.strip():
            metadata = {"source_file": source_filename, "data_type": data_type, "original_content_str": str(json_content)}
            chunks_with_metadata.append((text_to_embed, metadata))
            
    return chunks_with_metadata

def build_index_for_game(game_suffix: str, embedder: SSEMEmbedder):
    print(f"\n--- Building RAG Index for Game Suffix: '{game_suffix}' ---")
    all_texts = []
    all_metadata_for_index = []

    # 1. Process game-specific community files from RAW_DATA_INPUT_DIR
    community_pattern = os.path.join(CONFIG["raw_data_input_dir"], CONFIG["community_file_pattern_template"].format(game_suffix=game_suffix))
    community_files = glob.glob(community_pattern)
    print(f"Found {len(community_files)} community files for '{game_suffix}' matching '{community_pattern}'")
    for file_path in community_files:
        content = load_json_file(file_path)
        if content:
            chunks = extract_text_chunks_and_metadata(content, os.path.basename(file_path), f"community_{game_suffix}")
            for text, meta in chunks:
                all_texts.append(text)
                all_metadata_for_index.append(meta)

    if not all_texts:
        print(f"No text content extracted to build index for '{game_suffix}'. Skipping.")
        return

    print(f"Total text chunks to embed for '{game_suffix}': {len(all_texts)}")
    
    embeddings_np = embedder.generate_embeddings(all_texts) # SSEMEmbedder returns numpy array
    embeddings_np = np.asarray(embeddings_np, dtype=np.float32) # Ensure float32 for FAISS

    if embeddings_np.size == 0:
        print(f"Embedding generation resulted in an empty array for '{game_suffix}'. Skipping index creation.")
        return

    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dimension) 
    index.add(embeddings_np)
    print(f"FAISS index built for '{game_suffix}' with {index.ntotal} vectors (dimension: {dimension}).")

    # Save index and metadata
    os.makedirs(CONFIG["rag_index_output_dir"], exist_ok=True)
    faiss_path = os.path.join(CONFIG["rag_index_output_dir"], CONFIG["faiss_index_filename_template"].format(game_suffix=game_suffix))
    metadata_path = os.path.join(CONFIG["rag_index_output_dir"], CONFIG["metadata_filename_template"].format(game_suffix=game_suffix))

    faiss.write_index(index, faiss_path)
    print(f"FAISS index for '{game_suffix}' saved to: {faiss_path}")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(all_metadata_for_index, f, indent=2)
    print(f"Metadata for '{game_suffix}' saved to: {metadata_path}")

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