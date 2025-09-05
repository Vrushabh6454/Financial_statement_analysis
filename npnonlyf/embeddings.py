"""
Vector embeddings and semantic search functionality using sentence-transformers and FAISS.
"""

import os
import json
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Optional, Any
import logging

from utils import save_json, load_json

logger = logging.getLogger(__name__)


class FinancialEmbeddingsManager:
    """
    Manages vector embeddings for financial document text using FAISS.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', index_path: str = 'data/embeddings'):
        """
        Initialize embeddings manager.
        
        Args:
            model_name: Sentence transformer model name
            index_path: Path to store FAISS index and metadata
        """
        self.model_name = model_name
        self.index_path = index_path
        self.model = None
        self.index = None
        self.metadata = []
        self.dimension = None
        
        # Create embeddings directory
        os.makedirs(index_path, exist_ok=True)
        
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Embedding dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise
    
    def create_embeddings(self, notes_data: List[Dict]) -> None:
        """
        Create embeddings for notes text and build FAISS index.
        
        Args:
            notes_data: List of note text chunks with metadata
        """
        if not notes_data:
            logger.warning("No notes data provided for embedding creation")
            return
        
        logger.info(f"Creating embeddings for {len(notes_data)} text chunks...")
        
        # Extract text for embedding
        texts = [chunk['text'] for chunk in notes_data]
        
        try:
            # Generate embeddings
            logger.info("Generating embeddings...")
            embeddings = self.model.encode(
                texts, 
                show_progress_bar=True,
                batch_size=32,
                convert_to_numpy=True
            )
            
            logger.info(f"Generated {len(embeddings)} embeddings with dimension {embeddings.shape[1]}")
            
            # Create FAISS index
            self._create_faiss_index(embeddings)
            
            # Store metadata with the new schema
            self.metadata = []
            for i, chunk in enumerate(notes_data):
                metadata_entry = {
                    'id': i,
                    'company_id': chunk['company_id'],
                    'year': chunk['year'],
                    'section': chunk['section'],
                    'chunk_id': chunk['chunk_id'],
                    'page_no': chunk.get('page_no', 'N/A'),
                    'text': chunk['text'],
                    'length': chunk['length']
                }
                self.metadata.append(metadata_entry)
            
            # Save everything
            self._save_index_and_metadata()
            
            logger.info("Embeddings created and saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to create embeddings: {e}")
            raise
    
    def _create_faiss_index(self, embeddings: np.ndarray) -> None:
        """
        Create FAISS index from embeddings.
        
        Args:
            embeddings: NumPy array of embeddings
        """
        try:
            faiss.normalize_L2(embeddings)
            self.index = faiss.IndexFlatIP(embeddings.shape[1])
            self.index.add(embeddings.astype('float32'))
            
            logger.info(f"Created FAISS index with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Failed to create FAISS index: {e}")
            raise
    
    def _save_index_and_metadata(self) -> None:
        """Save FAISS index and metadata to disk."""
        try:
            index_file = os.path.join(self.index_path, 'notes.index')
            metadata_file = os.path.join(self.index_path, 'notes_meta.json')
            
            faiss.write_index(self.index, index_file)
            logger.info(f"Saved FAISS index to {index_file}")
            
            save_json(self.metadata, metadata_file)
            logger.info(f"Saved metadata to {metadata_file}")
            
        except Exception as e:
            logger.error(f"Failed to save index and metadata: {e}")
            raise
    
    def load_index_and_metadata(self) -> bool:
        """
        Load FAISS index and metadata from disk.
        """
        try:
            index_file = os.path.join(self.index_path, 'notes.index')
            metadata_file = os.path.join(self.index_path, 'notes_meta.json')
            
            if not os.path.exists(index_file) or not os.path.exists(metadata_file):
                logger.warning("Index or metadata file not found")
                return False
            
            self.index = faiss.read_index(index_file)
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            
            self.metadata = load_json(metadata_file)
            if self.metadata is None:
                logger.error("Failed to load metadata")
                return False
            
            logger.info(f"Loaded metadata for {len(self.metadata)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index and metadata: {e}")
            return False
    
    def semantic_search(self, query: str, top_k: int = 5, 
                       company_filter: Optional[str] = None,
                       year_filter: Optional[int] = None) -> List[Dict]:
        """
        Perform semantic search on the embedded notes.
        """
        if self.index is None or not self.metadata:
            logger.warning("Index not loaded. Cannot perform search.")
            return []
        
        try:
            query_embedding = self.model.encode([query], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)
            
            scores, indices = self.index.search(query_embedding.astype('float32'), 
                                              min(top_k * 3, len(self.metadata)))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:
                    continue
                
                metadata = self.metadata[idx]
                
                if company_filter and metadata['company_id'].lower() != company_filter.lower():
                    continue
                
                if year_filter and metadata['year'] != year_filter:
                    continue
                
                result = {
                    'score': float(score),
                    'company_id': metadata['company_id'],
                    'year': metadata['year'],
                    'section': metadata['section'],
                    'page_no': metadata['page_no'],
                    'text': metadata['text'],
                    'chunk_id': metadata['chunk_id']
                }
                
                results.append(result)
                
                if len(results) >= top_k:
                    break
            
            logger.info(f"Found {len(results)} results for query: '{query[:50]}...'")
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}")
            return []


def generate_answer_from_context(query: str, search_results: List[Dict]) -> str:
    """
    Generate a comprehensive answer from search results.
    """
    if not search_results:
        return "No relevant information found in the financial documents."
    
    context_parts = []
    companies_mentioned = set()
    years_mentioned = set()
    
    for i, result in enumerate(search_results[:3]):
        company_id = result['company_id']
        year = result['year']
        text = result['text']
        section = result['section']
        
        companies_mentioned.add(company_id)
        years_mentioned.add(str(year))
        
        if len(text) > 500:
            text = text[:500] + "..."
        
        context_parts.append(f"[{company_id} {year} - {section}]: {text}")
    
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['risk', 'risks', 'exposure']):
        answer_prefix = "Based on the risk disclosures and financial statements:"
    elif any(word in query_lower for word in ['revenue', 'sales', 'income']):
        answer_prefix = "Regarding financial performance:"
    elif any(word in query_lower for word in ['cash', 'liquidity', 'flow']):
        answer_prefix = "Concerning cash flow and liquidity:"
    elif any(word in query_lower for word in ['debt', 'leverage', 'borrowing']):
        answer_prefix = "Regarding debt and financing:"
    else:
        answer_prefix = "Based on the financial documents:"
    
    answer_parts = [answer_prefix]
    
    for part in context_parts:
        answer_parts.append(f"\n\n{part}")
    
    if len(companies_mentioned) == 1:
        company_text = f"for {list(companies_mentioned)[0]}"
    else:
        company_text = f"across {len(companies_mentioned)} companies"
    
    years_text = f"covering {min(years_mentioned)}-{max(years_mentioned)}" if len(years_mentioned) > 1 else f"for {list(years_mentioned)[0]}"
    
    answer_parts.append(f"\n\nThis information is {company_text} {years_text}.")
    
    return "".join(answer_parts)


def create_embeddings_pipeline(notes_data: List[Dict], index_path: str = 'data/embeddings') -> FinancialEmbeddingsManager:
    """
    Complete pipeline to create embeddings from notes data.
    """
    manager = FinancialEmbeddingsManager(index_path=index_path)
    manager.create_embeddings(notes_data)
    return manager