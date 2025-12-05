"""
System and iCloud scanning commands
"""
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from pathlib import Path

app = typer.Typer()
console = Console()

@app.command()
def icloud():
    """Scan and index your iCloud data (Drive, Photos, Messages, Contacts)"""
    try:
        from libs.icloud_sync import iCloudSync
        
        console.print("\n[bold blue]🍎 Starting iCloud Deep Scan...[/bold blue]\n")
        
        sync = iCloudSync()
        
        # Run all scans with progress bars
        drive = sync.scan_icloud_drive(show_progress=True)
        photos = sync.scan_photos_library(show_progress=True)
        messages = sync.scan_messages(show_progress=True)
        contacts = sync.scan_contacts()
        
        console.print("\n[bold green]✅ Scan Complete![/bold green]")
        console.print(f"\n📁 iCloud Drive: {drive.get('total', 0)} files")
        console.print(f"📸 Photos: {photos.get('total', 0)} images")
        console.print(f"💬 Messages: {messages.get('total', 0)} conversations")
        console.print(f"👥 Contacts: {contacts.get('total', 0)} people\n")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")

@app.command()
def system():
    """Deep scan your entire Mac filesystem"""
    console.print("\n[bold blue]🖥️  Starting System Deep Scan...[/bold blue]\n")
    
    from rich.progress import track
    import time
    
    home = Path.home()
    important_dirs = [
        home / "Desktop",
        home / "Documents", 
        home / "Downloads",
        home / "Pictures",
        home / "Movies"
    ]
    
    all_files = []
    
    for dir_path in important_dirs:
        if dir_path.exists():
            console.print(f"\n📂 Scanning {dir_path.name}...")
            files = list(dir_path.rglob("*"))
            
            for file in track(files, description=f"Indexing {dir_path.name}"):
                if file.is_file():
                    all_files.append(file)
                time.sleep(0.001)  # Smooth progress bar
    
    console.print(f"\n[bold green]✅ Found {len(all_files)} files total[/bold green]\n")

if __name__ == "__main__":
    app()
