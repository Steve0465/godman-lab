"""
iCloud integration for GodmanAI
Sync photos, contacts, messages, documents
"""
import os
from pathlib import Path
from typing import Optional
from tqdm import tqdm
import time

class iCloudSync:
    """Access iCloud data through official APIs and local sync"""
    
    def __init__(self, apple_id: Optional[str] = None):
        self.apple_id = apple_id or os.getenv("APPLE_ID")
        self.sync_dir = Path.home() / "Library" / "Mobile Documents"
        
    def scan_icloud_drive(self, show_progress: bool = True):
        """Scan iCloud Drive documents"""
        print("🔍 Scanning iCloud Drive...")
        
        icloud_path = self.sync_dir / "com~apple~CloudDocs"
        if not icloud_path.exists():
            return {"error": "iCloud Drive not synced locally"}
        
        files = list(icloud_path.rglob("*"))
        results = []
        
        if show_progress:
            for file in tqdm(files, desc="Indexing files", unit="files"):
                if file.is_file():
                    results.append({
                        "path": str(file),
                        "name": file.name,
                        "size": file.stat().st_size,
                        "modified": file.stat().st_mtime
                    })
        
        return {"total": len(results), "files": results}
    
    def scan_photos_library(self, show_progress: bool = True):
        """Access Photos library metadata"""
        print("📸 Scanning Photos library...")
        
        photos_db = Path.home() / "Pictures" / "Photos Library.photoslibrary"
        if not photos_db.exists():
            return {"error": "Photos library not found"}
        
        # Use osxphotos for proper access
        try:
            import osxphotos
            photosdb = osxphotos.PhotosDB()
            photos = photosdb.photos()
            
            results = []
            if show_progress:
                for photo in tqdm(photos, desc="Analyzing photos", unit="photos"):
                    results.append({
                        "uuid": photo.uuid,
                        "date": str(photo.date),
                        "location": photo.location if photo.location else None,
                        "persons": photo.persons,
                        "keywords": photo.keywords
                    })
            
            return {"total": len(results), "photos": results}
        except ImportError:
            return {"error": "Install: pip install osxphotos"}
    
    def scan_messages(self, show_progress: bool = True):
        """Access Messages database (read-only)"""
        print("💬 Scanning Messages...")
        
        messages_db = Path.home() / "Library" / "Messages" / "chat.db"
        if not messages_db.exists():
            return {"error": "Messages database not accessible"}
        
        try:
            import sqlite3
            conn = sqlite3.connect(f"file:{messages_db}?mode=ro", uri=True)
            cursor = conn.cursor()
            
            # Count messages
            cursor.execute("SELECT COUNT(*) FROM message")
            total = cursor.fetchone()[0]
            
            # Get recent messages with progress bar
            cursor.execute("""
                SELECT datetime(date/1000000000 + 978307200, 'unixepoch', 'localtime') as date,
                       text, is_from_me
                FROM message 
                ORDER BY date DESC 
                LIMIT 1000
            """)
            
            messages = []
            rows = cursor.fetchall()
            
            if show_progress:
                for row in tqdm(rows, desc="Processing messages", unit="msgs"):
                    messages.append({
                        "date": row[0],
                        "text": row[1],
                        "sent_by_me": bool(row[2])
                    })
            
            conn.close()
            return {"total": total, "recent": messages}
            
        except Exception as e:
            return {"error": f"Messages access failed: {str(e)}"}
    
    def scan_contacts(self):
        """Access Contacts database"""
        print("👥 Scanning Contacts...")
        
        contacts_db = Path.home() / "Library" / "Application Support" / "AddressBook" / "AddressBook-v22.abcddb"
        
        if not contacts_db.exists():
            return {"error": "Contacts database not found"}
        
        try:
            import sqlite3
            conn = sqlite3.connect(f"file:{contacts_db}?mode=ro", uri=True)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ZFIRSTNAME, ZLASTNAME, ZORGANIZATION
                FROM ZABCDRECORD
                WHERE ZFIRSTNAME IS NOT NULL
            """)
            
            contacts = []
            for row in tqdm(cursor.fetchall(), desc="Loading contacts", unit="contacts"):
                contacts.append({
                    "first_name": row[0],
                    "last_name": row[1],
                    "organization": row[2]
                })
            
            conn.close()
            return {"total": len(contacts), "contacts": contacts}
            
        except Exception as e:
            return {"error": f"Contacts access failed: {str(e)}"}

if __name__ == "__main__":
    sync = iCloudSync()
    
    print("\n" + "="*60)
    print("🍎 iCloud Data Scanner with Progress Bars")
    print("="*60 + "\n")
    
    # Scan everything with progress indicators
    drive_data = sync.scan_icloud_drive()
    print(f"\n✅ Found {drive_data.get('total', 0)} files in iCloud Drive\n")
    
    photos_data = sync.scan_photos_library()
    print(f"\n✅ Found {photos_data.get('total', 0)} photos\n")
    
    messages_data = sync.scan_messages()
    print(f"\n✅ Found {messages_data.get('total', 0)} messages\n")
    
    contacts_data = sync.scan_contacts()
    print(f"\n✅ Found {contacts_data.get('total', 0)} contacts\n")
