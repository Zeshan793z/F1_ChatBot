from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
from pathlib import Path
from typing import List, Tuple

class F1VectorStore:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.encoder = SentenceTransformer(model_name)
        self.index = None
        self.documents = []
        self.dimension = 384  # For all-MiniLM-L6-v2
        
    def create_index(self, texts: List[str]):
        """Create FAISS index from text documents"""
        self.documents = texts
        print(f"Creating index for {len(texts)} documents...")
        
        # Encode all texts
        embeddings = self.encoder.encode(texts, show_progress_bar=True)
        
        # Create FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        print(f"✅ Index created with {self.index.ntotal} vectors")
    
    def search(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """Search for relevant documents"""
        if self.index is None:
            return []
        
        query_embedding = self.encoder.encode([query])
        distances, indices = self.index.search(
            np.array(query_embedding).astype('float32'), 
            k
        )
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                results.append((self.documents[idx], float(distance)))
        
        return results