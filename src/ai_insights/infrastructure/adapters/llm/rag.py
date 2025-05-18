import os
import json
import faiss
import numpy as np

from src.ai_insights.infrastructure.adapters.llm.ssem_embedder import SSEMEmbedder

class RAGRetriever:
    def __init__(self, game_suffix: str, base_rag_index_path: str, embedder: SSEMEmbedder):
        """
        Initializes the RAGRetriever.

        Args:
            game_suffix (str): The game identifier (e.g., 'brawl', 'royale').
            base_rag_index_path (str): Path to the directory containing FAISS index and metadata.
                                       (e.g., 'data/processed/rag_indexes')
            embedder (SSEMEmbedder): An instance of SSEMEmbedder.
        """
        self.game_suffix = game_suffix
        self.embedder = embedder
        self.index = None
        self.metadata_store = []

        self.total_indexed_characters = 0

        faiss_file = os.path.join(base_rag_index_path, f"vector_store_{game_suffix}.faiss")
        metadata_file = os.path.join(base_rag_index_path, f"vector_store_metadata_{game_suffix}.json")

        if os.path.exists(faiss_file) and os.path.exists(metadata_file):
            print(f"RAGRetriever: Loading FAISS index from {faiss_file}")
            self.index = faiss.read_index(faiss_file)
            print(f"RAGRetriever: Loading metadata from {metadata_file}")
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self.metadata_store = json.load(f)
            print(f"RAGRetriever for '{game_suffix}': Index ({self.index.ntotal} vectors) and metadata ({len(self.metadata_store)} items) loaded.")

            if self.metadata_store and self.index:
                # Calculate total characters in the indexed corpus
                for meta_item in self.metadata_store:
                    # Assuming 'original_item' holds the content that was (or represents) what was embedded.
                    # The 'original_item' was stored in the metadata by data_embedder.py
                    original_item_content = meta_item.get("original_content_str") # Or "original_content"
                    if original_item_content:
                        try:
                            # A consistent way to get string length for dict/list/str
                            self.total_indexed_characters += len(json.dumps(original_item_content))
                        except TypeError: # Fallback if not directly serializable
                            self.total_indexed_characters += len(str(original_item_content))
                
                print(f"RAGRetriever for '{game_suffix}': Index ({self.index.ntotal} vectors) and metadata ({len(self.metadata_store)} items) loaded.")
                print(f"RAGRetriever: Approx. total characters in indexed corpus for '{game_suffix}': {self.total_indexed_characters:,}")
            else:
                print(f"RAGRetriever Warning: Index or metadata loaded but one might be empty for '{game_suffix}'.")

        else:
            print(f"RAGRetriever Error: Index or metadata file not found for game '{game_suffix}' in '{base_rag_index_path}'.")
            print(f"  Expected FAISS: {faiss_file}")
            print(f"  Expected Metadata: {metadata_file}")
            print("  RAG will not be functional for this game. Please run the data_embedder.py script.")



    def retrieve(self, query_text: str, top_k: int = 5) -> list[dict]:
        """
        Retrieves the top_k most relevant original content items for the given query_text.
        """
        if self.index is None or self.index.ntotal == 0:
            print("RAGRetriever: No index loaded or index is empty. Cannot retrieve.")
            return []
        if not query_text:
            print("RAGRetriever: Query text is empty. Cannot retrieve.")
            return []

        print(f"RAGRetriever: Generating embedding for query (first 500 chars): '{query_text[:500]}...'")
        query_embedding = self.embedder.generate_embeddings([query_text]) # Expects list, returns array
        query_embedding_np = np.asarray(query_embedding, dtype=np.float32)

        if query_embedding_np.size == 0:
            print("RAGRetriever: Failed to generate query embedding.")
            return []

        print(f"RAGRetriever: Searching index with {self.index.ntotal} vectors for top {top_k} results.")
        try:
            # FAISS search returns distances (D) and indices (I)
            # We need to ensure top_k is not greater than the number of items in index
            actual_k = min(top_k, self.index.ntotal)
            if actual_k == 0: return []

            distances, indices = self.index.search(query_embedding_np, actual_k)
        except Exception as e:
            print(f"RAGRetriever: Error during FAISS search: {e}")
            return []


        retrieved_text_chunks = []
        if indices.size > 0 and len(indices[0]) > 0:
            for i in indices[0]: 
                if i != -1 and 0 <= i < len(self.metadata_store):
                    current_chunk_metadata = self.metadata_store[i] # Metadata for a specific CHUNK
                    text_content_of_chunk = current_chunk_metadata.get("text_chunk")
                    
                    if text_content_of_chunk is None:
                        # Fallback: maybe the original small item (if not further chunked) was stored
                        original_item_dict = current_chunk_metadata.get("original_item_dict_as_chunk")
                        if isinstance(original_item_dict, dict):
                            title = original_item_dict.get("topic", original_item_dict.get("title", ""))
                            summary = original_item_dict.get("summary", "")
                            details = original_item_dict.get("raw_text", original_item_dict.get("full_text", original_item_dict.get("text", "")))
                            text_content_of_chunk = f"Title: {title}. Summary: {summary}. Details: {details}".strip()
                        elif isinstance(original_item_dict, str): # If it was already a string
                             text_content_of_chunk = original_item_dict
                        else: # Last resort if "original_item_str" was used for some unchunkable items
                            text_content_of_chunk = current_chunk_metadata.get("original_item_str")

                    if text_content_of_chunk:
                        retrieved_text_chunks.append(text_content_of_chunk)
                    else:
                        try:
                            retrieved_text_chunks.append(current_chunk_metadata['text_chunk_content'])
                        except:
                            retrieved_text_chunks.append(current_chunk_metadata)
                        # print(f"RAGRetriever WARNING: Could not extract retrievable text_chunk from metadata at index {i}. Metadata: {current_chunk_metadata}")

        num_retrieved_items = len(retrieved_text_chunks) 
        chars_in_retrieved_items = 0
        if num_retrieved_items > 0:
            for item_content in retrieved_text_chunks:
                try:
                    chars_in_retrieved_items += len(json.dumps(item_content))
                except TypeError:
                    chars_in_retrieved_items += len(str(item_content))

        print(f"RAGRetriever: Retrieved {num_retrieved_items} items relevant to the query.")
        print(f"RAGRetriever: Approx. total characters in retrieved items: {chars_in_retrieved_items:,}")
        
        print(f"RAGRetriever: Retrieved {len(retrieved_text_chunks)} items.")

        return retrieved_text_chunks
            

