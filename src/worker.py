"""
Worker pool for AutoSorter.

Manages a ThreadPoolExecutor that processes files through the
extract -> classify -> move pipeline. Maintains a processed file
registry to prevent duplicate processing.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

from src.config import PROCESSED_FILES_PATH, DATA_DIR, load_config, get_file_type
from src.extractors import extract_text
from src.mover import move_file
from src.logger import get_logger, log_file_result


class WorkerPool:
    """Thread pool that processes files through the classification pipeline.
    
    Each file is: extracted -> classified -> moved (if confident) or kept.
    Results are logged and files are tracked in a processed registry.
    """

    def __init__(self, classifier, config):
        """Initialize the worker pool.
        
        Args:
            classifier: ClassificationEngine instance (shared, thread-safe).
            config: Configuration dictionary from config.json.
        """
        self.classifier = classifier
        self.config = config
        self.logger = get_logger()
        self.threshold = config.get('confidence_threshold', 0.50)
        self.num_workers = config.get('worker_threads', 2)
        self.executor = ThreadPoolExecutor(max_workers=self.num_workers)
        self.processed_files = self._load_processed_files()
        
        self.logger.info(f"Worker pool initialized: {self.num_workers} workers, threshold={self.threshold}")

    def submit(self, filepath):
        """Submit a file for processing.
        
        Checks if the file was already processed before submitting.
        
        Args:
            filepath: Absolute path to the file to process.
        """
        filename = os.path.basename(filepath)
        
        # Check if already processed
        if self._is_already_processed(filepath):
            self.logger.debug(f"Skipping already-processed file: {filename}")
            return
        
        self.logger.info(f"Queuing file for processing: {filename}")
        self.executor.submit(self._process_file, filepath)

    def _process_file(self, filepath):
        """Process a single file through the full pipeline.
        
        Extract text -> Classify -> Move or Keep.
        All exceptions are caught to prevent worker thread crashes.
        
        Args:
            filepath: Absolute path to the file.
        """
        filename = os.path.basename(filepath)
        file_type = get_file_type(filepath) or "UNKNOWN"
        start_time = time.time()
        
        try:
            # Verify file still exists (could have been moved/deleted)
            if not os.path.exists(filepath):
                self.logger.warning(f"File no longer exists: {filename}")
                return

            # Step 1: Extract text
            self.logger.info(f"Extracting text from: {filename}")
            text = extract_text(filepath)
            
            if not text or not text.strip():
                elapsed = time.time() - start_time
                self.logger.warning(f"No text extracted from: {filename}")
                log_file_result(filename, file_type, "N/A", 0.0, "KEPT (no text)", elapsed)
                self._mark_processed(filepath)
                return
            
            # Step 2: Classify
            category, score = self.classifier.classify(text)
            
            # Step 3: Decide action
            elapsed = time.time() - start_time
            
            if score >= self.threshold:
                # Move file to subject folder
                dest = move_file(filepath, category)
                log_file_result(filename, file_type, category, score, "MOVED", elapsed)
                self.logger.info(f"MOVED {filename} -> {category}/ (score={score:.4f})")
            else:
                # Leave in Downloads
                log_file_result(filename, file_type, category, score, "KEPT", elapsed)
                self.logger.info(f"KEPT {filename} in Downloads (best={category}, score={score:.4f})")
            
            # Mark as processed
            self._mark_processed(filepath)
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"Error processing {filename}: {e}", exc_info=True)
            log_file_result(filename, file_type, "ERROR", 0.0, "ERROR", elapsed, error=str(e))

    def _is_already_processed(self, filepath):
        """Check if a file has already been processed.
        
        Compares filename and last modified time against the registry.
        
        Args:
            filepath: Absolute path to the file.
            
        Returns:
            bool: True if file was already processed with same mtime.
        """
        filename = os.path.basename(filepath)
        if filename not in self.processed_files:
            return False
        
        try:
            current_mtime = os.path.getmtime(filepath)
            recorded_mtime = self.processed_files[filename]
            return abs(current_mtime - recorded_mtime) < 1.0
        except OSError:
            return False

    def _mark_processed(self, filepath):
        """Add a file to the processed registry.
        
        Args:
            filepath: Absolute path to the file.
        """
        filename = os.path.basename(filepath)
        try:
            mtime = os.path.getmtime(filepath)
        except OSError:
            mtime = time.time()
        
        self.processed_files[filename] = mtime
        self._save_processed_files()

    def _load_processed_files(self):
        """Load the processed files registry from disk.
        
        Returns:
            dict: Mapping of filename -> last modified timestamp.
        """
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(PROCESSED_FILES_PATH):
            try:
                with open(PROCESSED_FILES_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                self.logger.warning(f"Could not load processed files registry: {e}")
        return {}

    def _save_processed_files(self):
        """Persist the processed files registry to disk."""
        try:
            with open(PROCESSED_FILES_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.processed_files, f, indent=2)
        except OSError as e:
            self.logger.error(f"Could not save processed files registry: {e}")

    def shutdown(self):
        """Gracefully shut down the worker pool.
        
        Waits for all queued tasks to complete before returning.
        """
        self.logger.info("Shutting down worker pool...")
        self.executor.shutdown(wait=True)
        self._save_processed_files()
        self.logger.info("Worker pool shut down successfully")
