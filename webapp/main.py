"""
FastAPI backend for the Enhanced OCR/Thread Analyzer web UI.

Provides endpoints for:
- File upload (images/videos)
- Processing management
- OCR results retrieval
- Human-in-the-loop corrections
- Export functionality

Run with: uvicorn webapp.main:app --reload
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Optional
import uuid
import shutil
import json
from datetime import datetime
import sqlite3
from contextlib import contextmanager

from prototype.enhanced.segmentation import BubbleSegmenter
from prototype.enhanced.ocr_backends import get_ocr_backend, get_available_backends

app = FastAPI(title="Enhanced OCR/Thread Analyzer", version="0.1.0")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / 'uploads'
STATIC_DIR = BASE_DIR / 'static'
TEMPLATE_DIR = BASE_DIR / 'templates'
DB_PATH = BASE_DIR / 'corrections.db'

UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATE_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Database setup
def init_db():
    """Initialize SQLite database for corrections."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            upload_time TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            preset TEXT DEFAULT 'imessage',
            backend TEXT DEFAULT 'tesseract'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bubbles (
            id TEXT PRIMARY KEY,
            upload_id TEXT NOT NULL,
            bubble_index INTEGER NOT NULL,
            x INTEGER,
            y INTEGER,
            width INTEGER,
            height INTEGER,
            original_text TEXT,
            corrected_text TEXT,
            confidence REAL,
            FOREIGN KEY (upload_id) REFERENCES uploads(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS threads (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_time TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS thread_messages (
            id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            bubble_id TEXT NOT NULL,
            message_order INTEGER,
            FOREIGN KEY (thread_id) REFERENCES threads(id),
            FOREIGN KEY (bubble_id) REFERENCES bubbles(id)
        )
    ''')
    
    conn.commit()
    conn.close()


@contextmanager
def get_db():
    """Get database connection context manager."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# Initialize DB on startup
init_db()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI."""
    html_file = TEMPLATE_DIR / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    else:
        return HTMLResponse("""
        <html>
        <head><title>Enhanced OCR/Thread Analyzer</title></head>
        <body>
            <h1>Enhanced OCR/Thread Analyzer</h1>
            <p>Web UI not yet configured. Please create webapp/templates/index.html</p>
            <p>API Documentation: <a href="/docs">/docs</a></p>
        </body>
        </html>
        """)


@app.get("/api/status")
async def get_status():
    """Get API status and available backends."""
    return {
        "status": "running",
        "version": "0.1.0",
        "available_backends": get_available_backends()
    }


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    preset: str = Form("imessage"),
    backend: str = Form("tesseract")
):
    """Upload an image for processing."""
    
    # Validate file type
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(400, f"Invalid file type. Allowed: {allowed_extensions}")
    
    # Generate unique ID
    upload_id = str(uuid.uuid4())
    upload_path = UPLOAD_DIR / upload_id
    upload_path.mkdir(exist_ok=True)
    
    # Save uploaded file
    file_path = upload_path / file.filename
    with open(file_path, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    
    # Save to database
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO uploads (id, filename, upload_time, status, preset, backend) VALUES (?, ?, ?, ?, ?, ?)',
            (upload_id, file.filename, datetime.now().isoformat(), 'uploaded', preset, backend)
        )
        conn.commit()
    
    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "status": "uploaded"
    }


@app.post("/api/process/{upload_id}")
async def process_upload(upload_id: str):
    """Process an uploaded image (segmentation + OCR)."""
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM uploads WHERE id = ?', (upload_id,))
        upload = cursor.fetchone()
        
        if not upload:
            raise HTTPException(404, "Upload not found")
        
        upload_path = UPLOAD_DIR / upload_id
        image_file = upload_path / upload['filename']
        
        if not image_file.exists():
            raise HTTPException(404, "Image file not found")
        
        # Update status
        cursor.execute('UPDATE uploads SET status = ? WHERE id = ?', ('processing', upload_id))
        conn.commit()
    
    try:
        # Segmentation
        segmenter = BubbleSegmenter(preset=upload['preset'])
        bubbles = segmenter.segment_image(str(image_file))
        
        # OCR
        ocr = get_ocr_backend(upload['backend'])
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            for i, bubble in enumerate(bubbles):
                # Save bubble crop
                crop_path = upload_path / f'bubble_{i}.png'
                bubble.save_crop(str(crop_path))
                
                # Run OCR
                ocr_result = ocr.extract_text(str(crop_path))
                
                # Save to database
                bubble_id = f"{upload_id}_{i}"
                cursor.execute('''
                    INSERT INTO bubbles 
                    (id, upload_id, bubble_index, x, y, width, height, original_text, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    bubble_id, upload_id, i,
                    bubble.x, bubble.y, bubble.width, bubble.height,
                    ocr_result.text, ocr_result.confidence
                ))
            
            # Update status
            cursor.execute('UPDATE uploads SET status = ? WHERE id = ?', ('completed', upload_id))
            conn.commit()
        
        return {
            "upload_id": upload_id,
            "status": "completed",
            "bubble_count": len(bubbles)
        }
    
    except Exception as e:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE uploads SET status = ? WHERE id = ?', ('failed', upload_id))
            conn.commit()
        
        raise HTTPException(500, f"Processing failed: {str(e)}")


@app.get("/api/uploads")
async def list_uploads():
    """List all uploads."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM uploads ORDER BY upload_time DESC')
        uploads = [dict(row) for row in cursor.fetchall()]
    
    return {"uploads": uploads}


@app.get("/api/uploads/{upload_id}")
async def get_upload(upload_id: str):
    """Get upload details with bubbles."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM uploads WHERE id = ?', (upload_id,))
        upload = cursor.fetchone()
        
        if not upload:
            raise HTTPException(404, "Upload not found")
        
        cursor.execute('SELECT * FROM bubbles WHERE upload_id = ? ORDER BY bubble_index', (upload_id,))
        bubbles = [dict(row) for row in cursor.fetchall()]
    
    return {
        "upload": dict(upload),
        "bubbles": bubbles
    }


@app.get("/api/uploads/{upload_id}/image")
async def get_upload_image(upload_id: str):
    """Get the original uploaded image."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT filename FROM uploads WHERE id = ?', (upload_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(404, "Upload not found")
        
        image_path = UPLOAD_DIR / upload_id / result['filename']
        
        if not image_path.exists():
            raise HTTPException(404, "Image file not found")
        
        return FileResponse(image_path)


@app.get("/api/bubbles/{bubble_id}/image")
async def get_bubble_image(bubble_id: str):
    """Get bubble crop image."""
    upload_id, bubble_index = bubble_id.rsplit('_', 1)
    image_path = UPLOAD_DIR / upload_id / f'bubble_{bubble_index}.png'
    
    if not image_path.exists():
        raise HTTPException(404, "Bubble image not found")
    
    return FileResponse(image_path)


@app.put("/api/bubbles/{bubble_id}/correction")
async def update_correction(bubble_id: str, corrected_text: str = Form(...)):
    """Update corrected text for a bubble."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE bubbles SET corrected_text = ? WHERE id = ?',
            (corrected_text, bubble_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(404, "Bubble not found")
    
    return {"bubble_id": bubble_id, "corrected_text": corrected_text}


@app.get("/api/export/{upload_id}")
async def export_thread(upload_id: str):
    """Export corrected thread as JSON."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM uploads WHERE id = ?', (upload_id,))
        upload = cursor.fetchone()
        
        if not upload:
            raise HTTPException(404, "Upload not found")
        
        cursor.execute('SELECT * FROM bubbles WHERE upload_id = ? ORDER BY bubble_index', (upload_id,))
        bubbles = cursor.fetchall()
        
        messages = []
        for bubble in bubbles:
            messages.append({
                'id': bubble['id'],
                'text': bubble['corrected_text'] or bubble['original_text'],
                'original_text': bubble['original_text'],
                'was_corrected': bubble['corrected_text'] is not None,
                'bounding_box': {
                    'x': bubble['x'],
                    'y': bubble['y'],
                    'width': bubble['width'],
                    'height': bubble['height']
                },
                'confidence': bubble['confidence']
            })
    
    return {
        'upload_id': upload_id,
        'filename': upload['filename'],
        'messages': messages,
        'export_time': datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
