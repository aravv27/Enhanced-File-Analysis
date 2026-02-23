# AutoSorter

**Automated Background Document Classification System**

A headless Windows background service that monitors your Downloads folder, classifies files by academic subject using sentence embeddings, and auto-sorts them into structured Desktop folders.

## How It Works

1. **Monitors** `Downloads/` for new files via watchdog
2. **Extracts text** from PDFs, DOCX, PPTX, images (OCR), and code files
3. **Classifies** using `all-MiniLM-L6-v2` sentence embeddings + cosine similarity
4. **Moves** high-confidence files to `Desktop/Subjects/<Category>/`
5. **Keeps** low-confidence files in Downloads untouched

## Supported File Types

| Type | Extensions |
|------|-----------|
| Documents | `.pdf`, `.docx`, `.pptx` |
| Images | `.jpg`, `.jpeg`, `.png` |
| Code | `.py`, `.ipynb`, `.c`, `.lex` |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python -m src.main

# Or install as startup service
install.bat
```

## Configuration

### `config/categories.json`
Edit this file to change subject categories. No retraining needed:
```json
{
  "RL": "Reinforcement Learning, Q-learning, policy gradient, MDP",
  "DL": "Deep Learning, neural networks, CNN, RNN, transformers"
}
```

### `config/config.json`
Runtime settings:
- `confidence_threshold`: Minimum similarity score to move a file (default: 0.50)
- `max_file_size_mb`: Skip files larger than this (default: 100)
- `worker_threads`: Concurrent processing threads (default: 2)
- `model_name`: Sentence transformer model (default: `all-MiniLM-L6-v2`)

## Requirements

- Python 3.8+
- Tesseract OCR (for scanned PDFs and images)
- ~500MB RAM at runtime

## Logs

Located at `%LOCALAPPDATA%\AutoSorter\logs\autosorter.log`
- Rotating: 5MB × 5 files
- Every processed file is logged with category, score, and action
