"""
AutoSorter — Main entry point.

Headless background service that monitors Downloads, classifies files
by academic subject using sentence embeddings, and auto-sorts them
into structured subject folders.

Usage:
    python -m src.main
    python -m src.main --config path/to/config.json
    
Or when packaged:
    AutoSorter.exe
"""

import argparse
import signal
import sys
import os

# Ensure project root is on path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import load_config, load_categories, ensure_directories, get_source_dir
from src.logger import setup_logging, get_logger
from src.classifier import ClassificationEngine
from src.worker import WorkerPool
from src.watcher import FileWatcher


class MockClassifier:
    """A mock classifier that returns instant results for stress testing."""
    
    def __init__(self, categories):
        self.category_names = list(categories.keys())
    
    def classify(self, text):
        """Return a fixed classification instantly."""
        return (self.category_names[0] if self.category_names else 'Unknown', 0.75)
    
    def precompute_categories(self, categories):
        """No-op for mock."""
        self.category_names = list(categories.keys())


def main(config_path=None):
    """Main startup orchestrator.
    
    1. Initialize logging
    2. Load configuration
    3. Ensure required directories exist
    4. Load embedding model and precompute category embeddings
    5. Start worker pool
    6. Start file watcher (blocks until shutdown)
    """
    # Step 1: Logging
    setup_logging()
    logger = get_logger()
    logger.info("=" * 60)
    logger.info("AutoSorter starting up...")
    logger.info("=" * 60)
    
    try:
        # Step 2: Load config
        config = load_config(config_path)
        categories = load_categories()
        logger.info(f"Configuration loaded: {len(categories)} categories")
        logger.info(f"Categories: {list(categories.keys())}")
        logger.info(f"Confidence threshold: {config.get('confidence_threshold', 0.50)}")
        
        # Step 3: Ensure directories
        ensure_directories()
        logger.info(f"Monitoring: {get_source_dir()}")
        
        # Step 4: Load model and precompute (or mock)
        if config.get('mock_classifier', False):
            logger.info("Using MOCK classifier (stress test mode)")
            engine = MockClassifier(categories)
        else:
            engine = ClassificationEngine(model_name=config.get('model_name', 'all-MiniLM-L6-v2'))
        engine.precompute_categories(categories)
        
        # Step 5: Start worker pool
        worker = WorkerPool(engine, config)
        
        # Step 6: Start watcher
        watcher = FileWatcher(worker, config, get_source_dir())
        
        # Register graceful shutdown handlers
        def shutdown_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            watcher.stop()
            worker.shutdown()
            logger.info("AutoSorter shut down successfully")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)
        
        logger.info("AutoSorter is running. Monitoring for new files...")
        
        # This blocks until stopped
        watcher.start()
        
    except Exception as e:
        logger.critical(f"Fatal error during startup: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AutoSorter')
    parser.add_argument('--config', type=str, default=None,
                        help='Path to custom config.json')
    args = parser.parse_args()
    main(config_path=args.config)
