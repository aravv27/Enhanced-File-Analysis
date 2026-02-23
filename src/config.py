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

# Resolved paths
DOWNLOADS_DIR = os.path.join(USER_HOME, 'Downloads')
SUBJECTS_DIR = os.path.join(USER_HOME, 'Desktop', 'Subjects')
APP_DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.join(USER_HOME, 'AppData', 'Local')), 'AutoSorter')
LOG_DIR = os.path.join(APP_DATA_DIR, 'logs')
DATA_DIR = APP_DATA_DIR

# Processed files registry path
PROCESSED_FILES_PATH = os.path.join(DATA_DIR, 'processed_files.json')

# Supported file extensions grouped by type
SUPPORTED_EXTENSIONS = {
    'documents': {'.pdf', '.docx', '.pptx'},
    'images': {'.jpg', '.jpeg', '.png'},
    'code': {'.py', '.ipynb', '.c', '.lex'},
}

ALL_SUPPORTED_EXTENSIONS = set()
for exts in SUPPORTED_EXTENSIONS.values():
    ALL_SUPPORTED_EXTENSIONS.update(exts)


def load_config():
    """Load runtime configuration from config/config.json.
    
    Returns:
        dict: Configuration dictionary with all runtime settings.
    """
    config_path = os.path.join(CONFIG_DIR, 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
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
        - Subjects directory on Desktop
        - AppData directory for logs and data
        - Log directory
    """
    for directory in [SUBJECTS_DIR, APP_DATA_DIR, LOG_DIR]:
        os.makedirs(directory, exist_ok=True)
