"""
Configuration loader for AutoSorter.

Loads config.json and categories.json from the config/ directory.
Resolves all paths dynamically based on the current user's home directory.
"""

import json
import os
import sys


def _get_base_dir():
    """Get the base directory of the application.
    
    When running as a PyInstaller bundle, uses the exe's directory.
    Otherwise, uses the project root (parent of src/).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = _get_base_dir()
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
USER_HOME = os.path.expanduser('~')
APP_DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.join(USER_HOME, 'AppData', 'Local')), 'AutoSorter')
LOG_DIR = os.path.join(APP_DATA_DIR, 'logs')
DATA_DIR = APP_DATA_DIR

# Processed files registry path
PROCESSED_FILES_PATH = os.path.join(DATA_DIR, 'processed_files.json')

# These are resolved at runtime from config.json via get_source_dir() / get_destination_dir()
_config_cache = None

def _get_config_cached():
    """Load config once and cache it."""
    global _config_cache
    if _config_cache is None:
        _config_cache = load_config()
    return _config_cache

def get_source_dir():
    """Get the source directory (Downloads) from config, with fallback."""
    config = _get_config_cached()
    return config.get('source_dir', os.path.join(USER_HOME, 'Downloads'))

def get_destination_dir():
    """Get the destination directory (Subjects) from config, with fallback."""
    config = _get_config_cached()
    return config.get('destination_dir', os.path.join(USER_HOME, 'Desktop', 'Subjects'))

# Supported file extensions grouped by type
SUPPORTED_EXTENSIONS = {
    'documents': {'.pdf', '.docx', '.pptx'},
    'images': {'.jpg', '.jpeg', '.png'},
    'code': {'.py', '.ipynb', '.c', '.lex'},
}

ALL_SUPPORTED_EXTENSIONS = set()
for exts in SUPPORTED_EXTENSIONS.values():
    ALL_SUPPORTED_EXTENSIONS.update(exts)


def load_config(config_path=None):
    """Load runtime configuration from config.json.
    
    Args:
        config_path: Optional path to a custom config file.
                     If None, loads from config/config.json.
    
    Returns:
        dict: Configuration dictionary with all runtime settings.
    """
    global _config_cache
    if config_path is None:
        config_path = os.path.join(CONFIG_DIR, 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    _config_cache = config  # Update cache so get_source_dir/get_destination_dir use this
    return config


def load_categories():
    """Load subject categories from config/categories.json.
    
    Returns:
        dict: Mapping of category name -> keyword description string.
    """
    categories_path = os.path.join(CONFIG_DIR, 'categories.json')
    with open(categories_path, 'r', encoding='utf-8') as f:
        categories = json.load(f)
    return categories


def get_file_type(filepath):
    """Determine the file type group for a given file path.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        str or None: 'documents', 'images', or 'code', or None if unsupported.
    """
    ext = os.path.splitext(filepath)[1].lower()
    for file_type, extensions in SUPPORTED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    return None


def ensure_directories():
    """Create all required directories if they don't exist.
    
    Creates:
        - Destination directory for subjects
        - AppData directory for logs and data
        - Log directory
    """
    for directory in [get_destination_dir(), APP_DATA_DIR, LOG_DIR]:
        os.makedirs(directory, exist_ok=True)
