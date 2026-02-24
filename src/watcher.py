"""
File system watcher for AutoSorter.

Uses the watchdog library to monitor the Downloads folder for new files.
Handles file readiness checks (waits for downloads to complete) and
filters by supported extensions before submitting to the worker pool.
"""

import os
import time
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from src.config import ALL_SUPPORTED_EXTENSIONS, load_config
from src.logger import get_logger


class FileWatcher:
    """Monitors the Downloads folder and submits new files for processing.
    
    Uses watchdog's Observer for event-driven file detection and handles
    file readiness (waiting for downloads to complete before processing).
    """

    def __init__(self, worker_pool, config, watch_dir):
        """Initialize the file watcher.
        
        Args:
            worker_pool: WorkerPool instance to submit files to.
            config: Configuration dictionary from config.json.
            watch_dir: Directory to monitor (typically Downloads).
        """
        self.worker_pool = worker_pool
        self.config = config
        self.watch_dir = watch_dir
        self.logger = get_logger()
        self.delay = config.get('watch_delay_seconds', 2)
        self.max_file_size = config.get('max_file_size_mb', 100) * 1024 * 1024  # Convert to bytes
        self.ignored_extensions = set(config.get('ignored_extensions', []))
        
        self.observer = Observer()
        self._handler = _NewFileHandler(self)
        self._recent_files = {}  # filepath -> timestamp for debounce
        self._debounce_seconds = 5
        
        self.logger.info(f"File watcher configured for: {watch_dir}")

    def start(self):
        """Start watching the Downloads folder. Blocks until stopped.
        
        Also performs an initial scan of existing files in the directory.
        """
        self.logger.info(f"Starting file watcher on: {self.watch_dir}")
        
        # Scan existing files if configured
        if self.config.get('scan_existing_on_startup', False):
            self._scan_existing()
        else:
            self.logger.info("Startup scan disabled — watching for new files only")
        
        self.observer.schedule(self._handler, self.watch_dir, recursive=False)
        self.observer.start()
        
        try:
            while self.observer.is_alive():
                self.observer.join(timeout=1)
        except KeyboardInterrupt:
            self.stop()

    def _scan_existing(self):
        """Scan the Downloads folder for existing supported files.
        
        Submits any supported files found to the worker pool.
        This catches files that were downloaded before the watcher started.
        """
        self.logger.info("Scanning existing files in Downloads...")
        count = 0
        try:
            for filename in os.listdir(self.watch_dir):
                filepath = os.path.join(self.watch_dir, filename)
                if not os.path.isfile(filepath):
                    continue
                
                ext = os.path.splitext(filename)[1].lower()
                if ext in self.ignored_extensions:
                    continue
                if ext not in ALL_SUPPORTED_EXTENSIONS:
                    continue
                
                # Check file size
                try:
                    file_size = os.path.getsize(filepath)
                    if file_size > self.max_file_size or file_size == 0:
                        continue
                except OSError:
                    continue
                
                self.worker_pool.submit(filepath)
                count += 1
        except OSError as e:
            self.logger.error(f"Error scanning Downloads: {e}")
        
        self.logger.info(f"Startup scan complete: {count} supported files found")

    def stop(self):
        """Stop the file watcher gracefully."""
        self.logger.info("Stopping file watcher...")
        self.observer.stop()
        self.observer.join()
        self.logger.info("File watcher stopped")

    def _on_new_file(self, filepath):
        """Handle a new file detection event.
        
        Debounces duplicate events (on_created + on_modified) for the same file.
        Validates extension, checks size, waits for file readiness,
        then submits to the worker pool.
        
        Args:
            filepath: Absolute path to the new file.
        """
        # Debounce: skip if we saw this file within the last N seconds
        now = time.time()
        if filepath in self._recent_files:
            if now - self._recent_files[filepath] < self._debounce_seconds:
                return
        self._recent_files[filepath] = now
        
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        
        # Filter ignored extensions (e.g., .crdownload)
        if ext in self.ignored_extensions:
            return
        
        # Filter unsupported extensions
        if ext not in ALL_SUPPORTED_EXTENSIONS:
            return
        
        self.logger.info(f"New file detected: {filename}")
        
        # Wait for file to be ready in a separate thread
        thread = threading.Thread(
            target=self._wait_and_submit,
            args=(filepath,),
            daemon=True
        )
        thread.start()

    def _wait_and_submit(self, filepath):
        """Wait for file to be ready, then submit for processing.
        
        Waits an initial delay, then retries access checks for up to 30s.
        
        Args:
            filepath: Absolute path to the file.
        """
        filename = os.path.basename(filepath)
        
        # Initial wait for download to settle
        time.sleep(self.delay)
        
        # Retry loop until file is accessible
        max_retries = 15
        retry_interval = 2  # seconds
        
        for attempt in range(max_retries):
            if not os.path.exists(filepath):
                self.logger.debug(f"File disappeared during wait: {filename}")
                return
            
            if self._is_file_ready(filepath):
                # Check file size
                try:
                    file_size = os.path.getsize(filepath)
                    if file_size > self.max_file_size:
                        self.logger.warning(
                            f"File too large ({file_size / 1024 / 1024:.1f}MB > "
                            f"{self.max_file_size / 1024 / 1024:.0f}MB): {filename}"
                        )
                        return
                    if file_size == 0:
                        self.logger.debug(f"Empty file, skipping: {filename}")
                        return
                except OSError:
                    continue
                
                # Submit to worker pool
                self.worker_pool.submit(filepath)
                return
            
            self.logger.debug(f"File not ready (attempt {attempt + 1}/{max_retries}): {filename}")
            time.sleep(retry_interval)
        
        self.logger.warning(f"File never became ready after {max_retries} attempts: {filename}")

    def _is_file_ready(self, filepath):
        """Check if a file is ready for processing (not locked by another process).
        
        Attempts to open the file in exclusive mode. If successful, the file
        is not being written to by another process.
        
        Args:
            filepath: Absolute path to the file.
            
        Returns:
            bool: True if file is accessible and not locked.
        """
        try:
            with open(filepath, 'rb') as f:
                # Try to read a small chunk to verify access
                f.read(1)
            return True
        except (OSError, IOError, PermissionError):
            return False


class _NewFileHandler(FileSystemEventHandler):
    """Watchdog event handler that delegates to FileWatcher."""

    def __init__(self, watcher):
        super().__init__()
        self.watcher = watcher

    def on_created(self, event):
        """Called when a file is created in the watched directory."""
        if event.is_directory:
            return
        self.watcher._on_new_file(event.src_path)

    def on_modified(self, event):
        """Called when a file is modified in the watched directory.
        
        Browsers sometimes create an empty file first, then write content,
        which triggers on_modified instead of on_created.
        """
        if event.is_directory:
            return
        self.watcher._on_new_file(event.src_path)
