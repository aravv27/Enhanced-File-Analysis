"""
Embedding-based classification engine for AutoSorter.

Loads a sentence-transformer model once at startup, precomputes category
embeddings from categories.json keywords, and classifies document text
via cosine similarity.

Uses a chunked approach: splits document text into overlapping chunks,
embeds each chunk, and takes the best similarity score across all chunks.
This produces much better scores than embedding entire documents at once.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.logger import get_logger

# Chunk configuration
CHUNK_SIZE_WORDS = 200       # Words per chunk
CHUNK_OVERLAP_WORDS = 50     # Overlap between consecutive chunks
MAX_CHUNKS = 20              # Maximum chunks to process per document


class ClassificationEngine:
    """Sentence-embedding-based document classifier.
    
    Loads a pretrained model and computes cosine similarity between
    document text embeddings and precomputed category embeddings.
    Thread-safe for concurrent inference.
    """

    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """Initialize the classification engine.
        
        Args:
            model_name: Name of the sentence-transformers model to load.
        """
        self.logger = get_logger()
        self.logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.logger.info("Embedding model loaded successfully")
        
        self.category_names = []
        self.category_embeddings = None

    def precompute_categories(self, categories_dict):
        """Precompute embeddings for all category keyword strings.
        
        Args:
            categories_dict: Dict mapping category name -> keyword description string.
                             e.g. {"RL": "Reinforcement Learning, Q-learning, ..."}
        """
        self.category_names = list(categories_dict.keys())
        keyword_strings = list(categories_dict.values())
        
        self.logger.info(f"Precomputing embeddings for {len(self.category_names)} categories: {self.category_names}")
        self.category_embeddings = self.model.encode(keyword_strings, convert_to_numpy=True)
        self.logger.info("Category embeddings precomputed successfully")

    def classify(self, text):
        """Classify a document's text against all categories.
        
        Splits text into overlapping chunks, embeds each chunk, computes
        cosine similarity against all categories, and returns the best
        (category, score) across all chunks. This chunked approach produces
        much higher similarity scores than embedding entire documents.
        
        Args:
            text: Extracted document text string.
            
        Returns:
            tuple: (category_name: str, similarity_score: float)
                   Returns the best matching category and its cosine similarity.
                   If no categories are loaded, returns ("UNKNOWN", 0.0).
        """
        if self.category_embeddings is None or len(self.category_names) == 0:
            self.logger.warning("No categories loaded — cannot classify")
            return ("UNKNOWN", 0.0)
        
        if not text or not text.strip():
            self.logger.warning("Empty text provided for classification")
            return ("UNKNOWN", 0.0)

        # Split text into chunks
        chunks = self._split_into_chunks(text)
        
        if not chunks:
            self.logger.warning("No chunks produced from text")
            return ("UNKNOWN", 0.0)
        
        self.logger.debug(f"Processing {len(chunks)} text chunks")
        
        # Encode all chunks in one batch for efficiency
        chunk_embeddings = self.model.encode(chunks, convert_to_numpy=True, batch_size=len(chunks))
        
        # Compute similarity of each chunk against all categories
        # Result shape: (num_chunks, num_categories)
        all_similarities = cosine_similarity(chunk_embeddings, self.category_embeddings)
        
        # For each category, take the max score across all chunks
        max_scores_per_category = np.max(all_similarities, axis=0)
        
        # Find best category
        best_idx = int(np.argmax(max_scores_per_category))
        best_category = self.category_names[best_idx]
        best_score = float(max_scores_per_category[best_idx])
        
        self.logger.debug(
            f"Classification scores (max across chunks): "
            f"{dict(zip(self.category_names, [f'{s:.4f}' for s in max_scores_per_category]))}"
        )
        
        return (best_category, best_score)

    def _split_into_chunks(self, text):
        """Split text into overlapping word-level chunks.
        
        Args:
            text: Full document text.
            
        Returns:
            list[str]: List of text chunks.
        """
        words = text.split()
        
        # If text is short enough, just return it as a single chunk
        if len(words) <= CHUNK_SIZE_WORDS:
            return [text]
        
        chunks = []
        step = CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS
        
        for i in range(0, len(words), step):
            chunk_words = words[i:i + CHUNK_SIZE_WORDS]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)
            
            if len(chunks) >= MAX_CHUNKS:
                break
        
        return chunks
