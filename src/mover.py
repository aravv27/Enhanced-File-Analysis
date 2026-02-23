"""
File movement logic for AutoSorter.

Handles moving classified files to Desktop/Subjects/<Category>/ with
filename conflict resolution (timestamp appending) and directory creation.
"""

import os
import shutil
from datetime import datetime

from src.config import SUBJECTS_DIR
from src.logger import get_logger


def move_file(filepath, category):
    """Move a file to the appropriate subject folder on Desktop.
    
    Creates the destination directory if it doesn't exist.
    If a file with the same name already exists, appends a timestamp
    to the filename to prevent overwriting.
    
    Args:
        filepath: Absolute path to the source file.
        category: Subject category name (used as folder name).
        
    Returns:
        str: Absolute path to the file's new location.
        
    Raises:
        OSError: If the move operation fails.
    """
    logger = get_logger()
    
    # Ensure destination directory exists
    dest_dir = os.path.join(SUBJECTS_DIR, category)
    os.makedirs(dest_dir, exist_ok=True)
    
    filename = os.path.basename(filepath)
    dest_path = os.path.join(dest_dir, filename)
    
    # Handle filename conflicts by appending timestamp
    if os.path.exists(dest_path):
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f"{name}_{timestamp}{ext}"
        dest_path = os.path.join(dest_dir, new_filename)
        logger.info(f"Filename conflict resolved: {filename} -> {new_filename}")
    
    shutil.move(filepath, dest_path)
    logger.info(f"Moved: {filename} -> {dest_path}")
    
    return dest_path
