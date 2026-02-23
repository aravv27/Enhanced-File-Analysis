"""
Embedding-based classification engine for AutoSorter.

Loads a sentence-transformer model once at startup, precomputes category
embeddings from categories.json keywords, and classifies document text
via cosine similarity.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.logger import get_logger


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

        # Truncate very long text to avoid embedding issues (max ~10000 chars)
        if len(text) > 10000:
            text = text[:10000]

        # Compute document embedding
        doc_embedding = self.model.encode([text], convert_to_numpy=True)
        
        # Compute cosine similarity against all categories
        similarities = cosine_similarity(doc_embedding, self.category_embeddings)[0]
        
        # Find best match
        best_idx = int(np.argmax(similarities))
        best_category = self.category_names[best_idx]
        best_score = float(similarities[best_idx])
        
        self.logger.debug(
            f"Classification scores: {dict(zip(self.category_names, [f'{s:.4f}' for s in similarities]))}"
        )
        
        return (best_category, best_score)
