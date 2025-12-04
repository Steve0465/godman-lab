# godman-lab
Personal automation lab for scripts, agents, and AI projects. Experiments, tools, and workflow systems.

## Enhanced OCR/Thread Analyzer

A comprehensive proof-of-concept system for extracting, analyzing, and visualizing text from messaging app screenshots.

### Features

- **🎯 Bubble Segmentation**: Heuristic OpenCV-based detection of message bubbles with presets for iMessage, WhatsApp, and Android SMS
- **📝 Multi-Backend OCR**: Support for local Tesseract, Google Cloud Vision, and AWS Textract with accuracy comparison tools
- **🌐 Web UI**: FastAPI backend with HTML/JS frontend for upload, processing, and human-in-the-loop correction
- **🧠 Semantic Analysis**: Sentence-transformers embeddings with FAISS indexing for similarity search and clustering
- **📊 Dashboard**: Streamlit-based visualization for sentiment analysis, topic discovery, and statistics

### Setup

#### Prerequisites

- Python 3.11+
- Tesseract OCR (for local processing)
- Optional: Google Cloud or AWS credentials for cloud OCR backends

#### Installation

1. Install dependencies:
```bash
pip install -r requirements-enhanced.txt

# Or install as a package with optional dependencies
pip install -e ".[all]"  # All features
pip install -e ".[webapp]"  # Just webapp
pip install -e ".[embeddings]"  # Just embeddings
```

2. Install Tesseract (Ubuntu/Debian):
```bash
sudo apt-get install tesseract-ocr
```

3. (Optional) Configure cloud backends:
```bash
# For Google Cloud Vision
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# For AWS Textract
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Usage

#### Quick Start - Process Screenshots

Process a folder of screenshots through the full pipeline:

```bash
cd prototype/enhanced
python process_folder.py /path/to/screenshots/ --output results/ --preset imessage
```

Options:
- `--preset`: UI preset (`generic`, `imessage`, `whatsapp`, `android_sms`)
- `--ocr`: OCR backend (`tesseract`, `google`, `aws`)
- `--no-embeddings`: Skip embedding generation

#### Compare OCR Backends

Run accuracy comparison across available backends:

```bash
cd prototype/enhanced
python compare_ocr_backends.py \
  --test-dir ../examples/ \
  --ground-truth ../examples/ground_truth.json \
  --output comparison.csv
```

#### Web UI and Dashboard

Start both the FastAPI backend and Streamlit dashboard:

```bash
# From repository root
./webapp/run_dev.sh
```

This starts:
- FastAPI Web UI at http://localhost:8000
- Streamlit Dashboard at http://localhost:8501

Or run them separately:

```bash
# FastAPI only
cd webapp
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Streamlit only
streamlit run webapp/dashboard/streamlit_app.py
```

#### Using Individual Modules

**Bubble Segmentation:**
```python
from segmentation import BubbleSegmenter, MessageUIPreset

segmenter = BubbleSegmenter(preset=MessageUIPreset.IMESSAGE)
bubbles = segmenter.segment_image('screenshot.png')

for i, bubble in enumerate(bubbles):
    bubble.save(f'bubble_{i}.png')
```

**OCR:**
```python
from ocr_backends import get_ocr_backend

backend = get_ocr_backend('tesseract')
result = backend.extract_text('image.png')
print(f"Text: {result.text}")
print(f"Confidence: {result.confidence:.2%}")
```

**Embeddings:**
```python
from embeddings import MessageEmbedder

embedder = MessageEmbedder()
embedder.add_messages(['Hello!', 'How are you?', 'Great to see you!'])

# Semantic search
results = embedder.search('greeting', k=2)
for idx, msg, distance, metadata in results:
    print(f"{msg} (distance: {distance:.3f})")

# Clustering
clusters = embedder.cluster_messages(n_clusters=3)
```

### Project Structure

```
prototype/
  enhanced/
    segmentation.py       # Bubble detection and extraction
    ocr_backends.py       # Unified OCR interface
    embeddings.py         # Semantic embeddings and search
    process_folder.py     # End-to-end processing CLI
    compare_ocr_backends.py  # Accuracy comparison tool
    tests/                # Unit tests
  examples/               # Test images and ground truth

webapp/
  api.py                  # FastAPI backend
  templates/
    index.html           # Web UI frontend
  dashboard/
    streamlit_app.py     # Streamlit dashboard
  run_dev.sh             # Development runner script
  uploads/               # Uploaded files (created at runtime)
  results/               # Processing results (created at runtime)
```

### Testing

Run unit tests:

```bash
cd prototype/enhanced
python -m pytest tests/ -v
```

### Privacy and Security Considerations

- **Local Processing**: Default Tesseract backend runs entirely locally
- **Cloud Backends**: Google Vision and AWS Textract send images to cloud services; ensure compliance with privacy requirements
- **Data Storage**: Uploaded images and OCR results are stored locally in `webapp/uploads/` and `webapp/results/`
- **Authentication**: Web UI is currently unauthenticated (PoC only); add authentication before production use
- **Sensitive Data**: Do not process screenshots containing passwords, financial data, or other sensitive information with cloud backends

### CI/CD

GitHub Actions workflow (`.github/workflows/enhanced-pipeline.yml`) runs on push/PR:
- Linting with flake8
- Unit tests with pytest
- Integration tests with example images

### Future Enhancements

- Support for video processing (frame extraction)
- Real-time processing with WebSocket updates
- Advanced NLP (named entity recognition, summarization)
- Multi-language support
- Export to various formats (PDF, CSV, etc.)
- User authentication and multi-tenant support
