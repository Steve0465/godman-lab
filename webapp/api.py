"""
FastAPI backend for OCR correction web UI.

Provides endpoints for:
- Uploading images/videos
- Running segmentation and OCR
- Viewing and correcting OCR results
- Exporting corrected data

Example usage:
    uvicorn api:app --reload
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import aiosqlite
import json
import os
import sys
import shutil
import uuid
from datetime import datetime

# Add prototype/enhanced to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'enhanced'))

from segmentation import BubbleSegmenter, MessageUIPreset
from ocr_backends import get_ocr_backend, get_available_backends

app = FastAPI(title="OCR Thread Analyzer", version="1.0.0")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("webapp/uploads")
RESULTS_DIR = Path("webapp/results")
DB_PATH = Path("webapp/corrections.db")

# Create directories
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Pydantic models
class CorrectionRequest(BaseModel):
    image_id: str
    bubble_index: int
    corrected_text: str

class ProcessRequest(BaseModel):
    image_id: str
    preset: str = "generic"
    ocr_backend: str = "tesseract"


# Database initialization
async def init_db():
    """Initialize SQLite database."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT 0,
                preset TEXT,
                ocr_backend TEXT
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bubbles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id TEXT NOT NULL,
                bubble_index INTEGER NOT NULL,
                x INTEGER,
                y INTEGER,
                width INTEGER,
                height INTEGER,
                original_text TEXT,
                corrected_text TEXT,
                confidence REAL,
                FOREIGN KEY (image_id) REFERENCES images(id)
            )
        """)
        
        await db.commit()


@app.on_event("startup")
async def startup_event():
    """Run on startup."""
    await init_db()


@app.get("/")
async def root():
    """Serve the main UI."""
    return FileResponse("webapp/templates/index.html")


@app.get("/api/backends")
async def get_backends():
    """Get available OCR backends."""
    backends = get_available_backends()
    return {
        "backends": [
            {
                "name": b.name,
                "available": True
            }
            for b in backends
        ]
    }


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload an image file."""
    # Generate unique ID
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix
    
    # Save file
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Store in database
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO images (id, filename) VALUES (?, ?)",
            (file_id, file.filename)
        )
        await db.commit()
    
    return {
        "id": file_id,
        "filename": file.filename,
        "status": "uploaded"
    }


@app.post("/api/process")
async def process_image(request: ProcessRequest):
    """Process an uploaded image."""
    # Check if image exists
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT filename FROM images WHERE id = ?",
            (request.image_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Image not found")
            
            filename = row[0]
    
    # Find the image file
    image_path = None
    for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
        potential_path = UPLOAD_DIR / f"{request.image_id}{ext}"
        if potential_path.exists():
            image_path = potential_path
            break
    
    if not image_path:
        raise HTTPException(status_code=404, detail="Image file not found")
    
    # Initialize segmenter and OCR
    preset_map = {
        'imessage': MessageUIPreset.IMESSAGE,
        'whatsapp': MessageUIPreset.WHATSAPP,
        'android_sms': MessageUIPreset.ANDROID_SMS,
        'generic': MessageUIPreset.GENERIC
    }
    
    segmenter = BubbleSegmenter(preset=preset_map.get(request.preset, MessageUIPreset.GENERIC))
    
    backend = get_ocr_backend(request.ocr_backend)
    if backend is None:
        # Fall back to any available backend
        available = get_available_backends()
        if not available:
            raise HTTPException(status_code=500, detail="No OCR backends available")
        backend = available[0]
    
    # Segment bubbles
    bubbles = segmenter.segment_image(str(image_path))
    
    # Process each bubble
    bubble_results = []
    
    for i, bubble in enumerate(bubbles):
        # Save bubble image
        bubble_path = RESULTS_DIR / request.image_id / f"bubble_{i}.png"
        bubble_path.parent.mkdir(parents=True, exist_ok=True)
        bubble.save(str(bubble_path))
        
        # Run OCR
        ocr_result = backend.extract_text(str(bubble_path))
        
        bubble_data = {
            'index': i,
            'bbox': bubble.to_dict(),
            'text': ocr_result.text,
            'confidence': ocr_result.confidence
        }
        bubble_results.append(bubble_data)
    
    # Store results in database
    async with aiosqlite.connect(DB_PATH) as db:
        # Update image record
        await db.execute(
            "UPDATE images SET processed = 1, preset = ?, ocr_backend = ? WHERE id = ?",
            (request.preset, backend.name, request.image_id)
        )
        
        # Insert bubble records
        for bubble in bubble_results:
            await db.execute(
                """INSERT INTO bubbles 
                   (image_id, bubble_index, x, y, width, height, original_text, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    request.image_id,
                    bubble['index'],
                    bubble['bbox']['x'],
                    bubble['bbox']['y'],
                    bubble['bbox']['width'],
                    bubble['bbox']['height'],
                    bubble['text'],
                    bubble['confidence']
                )
            )
        
        await db.commit()
    
    return {
        "image_id": request.image_id,
        "num_bubbles": len(bubble_results),
        "bubbles": bubble_results
    }


@app.get("/api/images")
async def list_images():
    """List all uploaded images."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, filename, uploaded_at, processed FROM images ORDER BY uploaded_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            
            images = []
            for row in rows:
                images.append({
                    'id': row[0],
                    'filename': row[1],
                    'uploaded_at': row[2],
                    'processed': bool(row[3])
                })
            
            return {"images": images}


@app.get("/api/images/{image_id}")
async def get_image_results(image_id: str):
    """Get OCR results for an image."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Get image info
        async with db.execute(
            "SELECT filename, processed, preset, ocr_backend FROM images WHERE id = ?",
            (image_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Image not found")
            
            image_info = {
                'id': image_id,
                'filename': row[0],
                'processed': bool(row[1]),
                'preset': row[2],
                'ocr_backend': row[3]
            }
        
        # Get bubbles
        async with db.execute(
            """SELECT bubble_index, x, y, width, height, original_text, 
                      corrected_text, confidence
               FROM bubbles WHERE image_id = ? ORDER BY bubble_index""",
            (image_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            
            bubbles = []
            for row in rows:
                bubbles.append({
                    'index': row[0],
                    'bbox': {
                        'x': row[1],
                        'y': row[2],
                        'width': row[3],
                        'height': row[4]
                    },
                    'original_text': row[5],
                    'corrected_text': row[6],
                    'confidence': row[7]
                })
            
            image_info['bubbles'] = bubbles
            
            return image_info


@app.post("/api/corrections")
async def save_correction(correction: CorrectionRequest):
    """Save a correction for a bubble."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE bubbles SET corrected_text = ? 
               WHERE image_id = ? AND bubble_index = ?""",
            (correction.corrected_text, correction.image_id, correction.bubble_index)
        )
        await db.commit()
    
    return {"status": "success"}


@app.get("/api/export/{image_id}")
async def export_thread(image_id: str):
    """Export corrected thread as JSON."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Get image info
        async with db.execute(
            "SELECT filename FROM images WHERE id = ?",
            (image_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Image not found")
            filename = row[0]
        
        # Get bubbles with corrections
        async with db.execute(
            """SELECT bubble_index, x, y, width, height, original_text, 
                      corrected_text, confidence
               FROM bubbles WHERE image_id = ? ORDER BY bubble_index""",
            (image_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            
            messages = []
            for row in rows:
                text = row[6] if row[6] else row[5]  # Use corrected text if available
                messages.append({
                    'index': row[0],
                    'text': text,
                    'original_text': row[5],
                    'confidence': row[7],
                    'bbox': {
                        'x': row[1],
                        'y': row[2],
                        'width': row[3],
                        'height': row[4]
                    }
                })
    
    export_data = {
        'image_id': image_id,
        'source_file': filename,
        'exported_at': datetime.now().isoformat(),
        'num_messages': len(messages),
        'messages': messages
    }
    
    return export_data


@app.get("/api/uploads/{image_id}")
async def get_uploaded_image(image_id: str):
    """Get the uploaded image file."""
    for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
        image_path = UPLOAD_DIR / f"{image_id}{ext}"
        if image_path.exists():
            return FileResponse(image_path)
    
    raise HTTPException(status_code=404, detail="Image not found")


@app.get("/api/bubbles/{image_id}/{bubble_index}")
async def get_bubble_image(image_id: str, bubble_index: int):
    """Get a specific bubble image."""
    bubble_path = RESULTS_DIR / image_id / f"bubble_{bubble_index}.png"
    
    if not bubble_path.exists():
        raise HTTPException(status_code=404, detail="Bubble image not found")
    
    return FileResponse(bubble_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
