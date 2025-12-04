# godman-lab
Personal automation lab for scripts, agents, and AI projects. Experiments, tools, and workflow systems.

---

## Enhanced OCR/Thread Analyzer

An end-to-end proof-of-concept for screenshot and screen-recording ingestion, message bubble detection, OCR extraction, and thread analysis with human-in-the-loop correction capabilities.

### Features

- **🔍 Bubble Segmentation**: Automatic detection of message bubbles in screenshots using OpenCV with presets for iMessage, WhatsApp, and Android SMS
- **📝 Multi-Backend OCR**: Unified interface supporting local Tesseract, Google Cloud Vision, and AWS Textract
- **🧠 Semantic Search**: Message embeddings using sentence-transformers with FAISS indexing for similarity search
- **📊 Analytics Dashboard**: Interactive Streamlit dashboard with sentiment analysis, topic clustering, and search
- **✏️ Web UI**: FastAPI-powered web interface for upload, processing, and human-in-the-loop text correction
- **🔐 Privacy-First**: Cloud backends are optional; all processing can run locally with Tesseract

### Quick Start

#### Installation

```bash
# Install dependencies
pip install -r requirements-enhanced.txt

# Install Tesseract (for local OCR)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract

# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

#### Processing Screenshots

Process a folder of screenshots through the full pipeline:

```bash
python prototype/enhanced/process_folder.py screenshots/ output/ --preset imessage --backend tesseract
```

Options:
- `--preset`: `imessage`, `whatsapp`, or `android_sms`
- `--backend`: `tesseract`, `google_vision`, or `aws_textract`
- `--skip-embedding`: Skip embedding computation

#### Running the Web UI

Start both the FastAPI backend and Streamlit dashboard:

```bash
# Quick start (runs both services)
bash webapp/run_dev.sh

# Or manually:
# Terminal 1 - FastAPI backend
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Streamlit dashboard
streamlit run webapp/dashboard/streamlit_app.py --server.port 8501
```

Access points:
- **Web UI**: http://localhost:8000
- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

#### Comparing OCR Backends

Test accuracy of different OCR backends on labeled data:

```bash
python prototype/enhanced/compare_ocr_backends.py prototype/examples/ prototype/examples/labels.json --output comparison.json
```

### Module Overview

#### `prototype/enhanced/segmentation.py`
Heuristic OpenCV-based bubble detection with configurable presets for different messaging platforms.

```python
from prototype.enhanced.segmentation import BubbleSegmenter

segmenter = BubbleSegmenter(preset='imessage')
bubbles = segmenter.segment_image('screenshot.png')

for bubble in bubbles:
    bubble.save_crop(f'bubble_{bubble.y}.png')
```

#### `prototype/enhanced/ocr_backends.py`
Unified OCR interface with multiple backend implementations.

```python
from prototype.enhanced.ocr_backends import get_ocr_backend

backend = get_ocr_backend('tesseract')
result = backend.extract_text('image.png')
print(f"Text: {result.text}")
print(f"Confidence: {result.confidence:.2%}")
```

#### `prototype/enhanced/embeddings.py`
Message embeddings for semantic search and clustering.

```python
from prototype.enhanced.embeddings import MessageEmbeddings

embedder = MessageEmbeddings()
embedder.add_messages([
    {'id': '1', 'text': 'Hello world'},
    {'id': '2', 'text': 'Good morning'}
])

# Semantic search
results = embedder.search('greeting', k=5)

# Topic clustering
clusters = embedder.cluster(n_clusters=3)
```

### Cloud Backend Configuration

#### Google Cloud Vision

```bash
# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Use in processing
python prototype/enhanced/process_folder.py input/ output/ --backend google_vision
```

#### AWS Textract

```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# Use in processing
python prototype/enhanced/process_folder.py input/ output/ --backend aws_textract
```

If cloud credentials are not configured, the system gracefully falls back to Tesseract.

### Web UI Features

1. **Upload & Process**: Upload screenshots and automatically detect message bubbles
2. **View & Correct**: Review OCR'd text with original bubble images side-by-side
3. **Edit Inline**: Click on any text field to make corrections
4. **Export**: Download corrected message threads as JSON

### Dashboard Features

The Streamlit dashboard provides:

- **Overview**: Message count, average OCR confidence, and sample messages
- **Sentiment Analysis**: Per-message sentiment scores with trend visualization
- **Topic Clustering**: Automatic topic detection using K-means clustering
- **Semantic Search**: Find messages by meaning, not just keywords

### Privacy & Security Considerations

- All processing can run entirely locally with Tesseract OCR
- Cloud backends (Google Vision, AWS Textract) are optional and require explicit configuration
- No data is sent to external services unless cloud backends are explicitly enabled
- The web UI stores data locally in SQLite (no external database required)
- For production use, add authentication to FastAPI endpoints (currently auth-free for PoC)

### Testing

Run the unit tests:

```bash
# Run all tests
pytest prototype/enhanced/tests/ -v

# Run with coverage
pytest prototype/enhanced/tests/ -v --cov=prototype.enhanced --cov-report=html

# Run specific test file
pytest prototype/enhanced/tests/test_segmentation.py -v
```

### Directory Structure

```
prototype/enhanced/
├── __init__.py
├── segmentation.py          # Bubble detection
├── ocr_backends.py          # OCR interface & implementations
├── embeddings.py            # Semantic search & clustering
├── process_folder.py        # End-to-end pipeline CLI
├── compare_ocr_backends.py  # Backend comparison tool
└── tests/                   # Unit tests
    ├── test_segmentation.py
    └── test_ocr_backends.py

webapp/
├── main.py                  # FastAPI backend
├── run_dev.sh              # Development startup script
├── templates/
│   └── index.html          # Web UI frontend
└── dashboard/
    └── streamlit_app.py    # Analytics dashboard

prototype/examples/
├── test_image1.png         # Example screenshots
├── test_image2.png
└── labels.json             # Ground truth labels
```

### Contributing

This is a proof-of-concept implementation. Areas for improvement:

- More sophisticated bubble detection (e.g., using ML models)
- Better OCR post-processing (spell check, context-aware correction)
- Video frame extraction and processing
- Multi-language support
- User authentication for web UI
- Database migration for production use

### License

This project is part of the godman-lab personal automation toolkit.
