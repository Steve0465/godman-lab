# Enhanced OCR/Thread Analyzer - Quick Reference

## Installation

```bash
pip install -r requirements-enhanced.txt

# Install Tesseract OCR (local backend)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract
```

## Command-Line Usage

### Process Screenshots

```bash
# Basic usage with Tesseract
python prototype/enhanced/process_folder.py screenshots/ output/ \
    --preset imessage \
    --backend tesseract

# With cloud backend (requires credentials)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
python prototype/enhanced/process_folder.py screenshots/ output/ \
    --preset whatsapp \
    --backend google_vision

# Skip embeddings for faster processing
python prototype/enhanced/process_folder.py screenshots/ output/ \
    --preset android_sms \
    --backend tesseract \
    --skip-embedding
```

### Segment Only

```bash
# Just extract bubble crops
python prototype/enhanced/segmentation.py screenshots/ bubbles/ --preset imessage
```

### Compare OCR Backends

```bash
# Test accuracy on labeled data
python prototype/enhanced/compare_ocr_backends.py \
    prototype/examples/ \
    prototype/examples/labels.json \
    --output comparison.json
```

### OCR Backend Tools

```bash
# List available backends
python prototype/enhanced/ocr_backends.py list

# Extract text from single image
python prototype/enhanced/ocr_backends.py extract image.png --backend tesseract

# Compare backends on test set
python prototype/enhanced/ocr_backends.py compare \
    test_images/ \
    labels.json \
    --output results.json
```

### Embeddings

```bash
# Create embeddings from messages
python prototype/enhanced/embeddings.py create messages.json embeddings.pkl

# Search messages
python prototype/enhanced/embeddings.py search embeddings.pkl "greeting" --k 5

# Cluster messages
python prototype/enhanced/embeddings.py cluster embeddings.pkl --n 5 --output clusters.json
```

## Web Interface

### Start Development Servers

```bash
# Start both FastAPI and Streamlit
bash webapp/run_dev.sh

# Or start individually:

# Terminal 1 - FastAPI backend
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Streamlit dashboard  
streamlit run webapp/dashboard/streamlit_app.py --server.port 8501
```

### Access Points

- **Web UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

### Web UI Workflow

1. Upload screenshot (PNG, JPG)
2. Select platform preset (iMessage, WhatsApp, Android SMS)
3. Select OCR backend
4. Click "Upload & Process"
5. Review detected bubbles and OCR text
6. Edit any incorrect text
7. Save corrections
8. Export as JSON

## Python API

### Segmentation

```python
from prototype.enhanced.segmentation import BubbleSegmenter

segmenter = BubbleSegmenter(preset='imessage')
bubbles = segmenter.segment_image('screenshot.png')

for i, bubble in enumerate(bubbles):
    print(f"Bubble {i}: {bubble.width}x{bubble.height} at ({bubble.x}, {bubble.y})")
    bubble.save_crop(f'bubble_{i}.png')
```

### OCR

```python
from prototype.enhanced.ocr_backends import get_ocr_backend

backend = get_ocr_backend('tesseract')
result = backend.extract_text('image.png')

print(f"Text: {result.text}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Words: {result.word_count}")
```

### Embeddings

```python
from prototype.enhanced.embeddings import MessageEmbeddings

embedder = MessageEmbeddings()
embedder.add_messages([
    {'id': '1', 'text': 'Hello world'},
    {'id': '2', 'text': 'Good morning'},
    {'id': '3', 'text': 'How are you?'}
])

# Search
results = embedder.search('greeting', k=2)
for msg, distance in results:
    print(f"{msg.text} (distance: {distance:.3f})")

# Cluster
clusters = embedder.cluster(n_clusters=2)
for cluster_id, messages in clusters.items():
    print(f"Cluster {cluster_id}: {len(messages)} messages")

# Save
embedder.save('embeddings.pkl')
```

## Cloud Backend Configuration

### Google Cloud Vision

```bash
# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Verify
python prototype/enhanced/ocr_backends.py list
```

### AWS Textract

```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# Verify
python prototype/enhanced/ocr_backends.py list
```

## Testing

```bash
# Run all tests
pytest prototype/enhanced/tests/ -v

# Run with coverage
pytest prototype/enhanced/tests/ --cov=prototype.enhanced --cov-report=html

# Run specific test
pytest prototype/enhanced/tests/test_segmentation.py -v
```

## Common Issues

### ImportError: No module named 'prototype'

Set PYTHONPATH to repository root:
```bash
export PYTHONPATH=/path/to/godman-lab
# or
PYTHONPATH=/path/to/godman-lab python script.py
```

### Tesseract not found

Install Tesseract OCR:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### huggingface.co connection errors

Embeddings require internet access to download models on first use.
The model is cached locally after first download.

### Cloud backends not available

Ensure credentials are properly configured:
- Google: `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- AWS: `aws configure` or AWS environment variables

The system gracefully falls back to Tesseract if cloud credentials are missing.

## Output Files

### Segmentation Output

```
output/
  segments/
    test_image1/
      bubble_000.png
      bubble_001.png
      metadata.json
    test_image2/
      bubble_000.png
      metadata.json
  processing_stats.json
```

### Pipeline Output

```
output/
  segments/           # Bubble crops
  ocr_results.json    # Raw OCR output
  processed_messages.json  # Messages with sentiment
  embeddings.pkl      # Embeddings (if enabled)
  topics.json         # Topic clusters (if enabled)
```

### Web UI Output

```
webapp/
  uploads/
    <upload-id>/
      original_image.png
      bubble_0.png
      bubble_1.png
  corrections.db      # SQLite database
```
