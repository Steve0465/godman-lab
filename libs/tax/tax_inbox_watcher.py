"""
Tax Inbox Watcher - Automatic file processing for tax archive inbox.

This module monitors the _inbox directory and automatically processes new files
by classifying them and routing them to the appropriate year/category folders.

Features:
- Debounced file event processing (default 30 seconds)
- Automatic classification using TaxClassifier
- Safe auto-apply for high-confidence moves
- Review queue for low-confidence classifications
- Structured logging with classification evidence
- Ignores temporary and system files

Safety guarantees:
- Never deletes files
- Never processes files still being written
- Never moves files outside _inbox unless part of deduplication
- All operations wrapped in error handling
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Set
from collections import defaultdict

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent

from .tax_sync import TaxSync
from .tax_classifier import TaxClassifier


# Files to ignore during processing
IGNORED_EXTENSIONS = {'.part', '.tmp', '.crdownload', '.download'}
IGNORED_FILENAMES = {'.DS_Store', 'Thumbs.db', 'desktop.ini', '.localized'}


class TaxInboxWatcher:
    """
    Monitors the _inbox directory and automatically processes new tax documents.
    
    This watcher uses a debounce mechanism to batch file events and process them
    together after a configurable wait period. Files are classified using the
    TaxClassifier and then routed using TaxSync.
    
    Auto-apply behavior:
    - High-confidence moves to YYYY/category: auto-applied
    - Moves to _metadata/misc: auto-applied
    - Moves to _metadata/duplicates: auto-applied
    - Low-confidence moves to _metadata/review: logged, safe moves applied
    
    Usage:
        watcher = TaxInboxWatcher(root_path)
        watcher.start()  # Blocks until stopped
    """
    
    def __init__(
        self,
        root_path: Path,
        debounce_seconds: int = 30,
        min_file_age_seconds: int = 5
    ):
        """
        Initialize the inbox watcher.
        
        Args:
            root_path: Root of the tax archive (contains _inbox)
            debounce_seconds: Wait time after last file event before processing
            min_file_age_seconds: Minimum age of file before processing (ensures write complete)
        """
        self.root_path = Path(root_path)
        self.inbox_path = self.root_path / "_inbox"
        self.debounce_seconds = debounce_seconds
        self.min_file_age_seconds = min_file_age_seconds
        
        # Ensure required directories exist
        self.inbox_path.mkdir(parents=True, exist_ok=True)
        (self.root_path / "_metadata" / "logs").mkdir(parents=True, exist_ok=True)
        (self.root_path / "_metadata" / "review").mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.tax_sync = TaxSync(self.root_path)
        self.tax_classifier = TaxClassifier()
        
        # Setup logging
        self._setup_logging()
        
        # Event tracking
        self.pending_files: Set[Path] = set()
        self.last_event_time: float = 0
        self.observer = None
        
    def _setup_logging(self):
        """Configure structured logging to daily log files."""
        log_dir = self.root_path / "_metadata" / "logs"
        log_file = log_dir / f"inbox_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Create a logger specific to this watcher
        self.logger = logging.getLogger(f"TaxInboxWatcher.{self.root_path.name}")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler with detailed formatting
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
    def _is_ignored_file(self, path: Path) -> bool:
        """Check if file should be ignored based on extension or name."""
        if path.suffix.lower() in IGNORED_EXTENSIONS:
            return True
        if path.name in IGNORED_FILENAMES:
            return True
        return False
    
    def _is_file_stable(self, path: Path) -> bool:
        """
        Check if file is stable (not currently being written).
        
        A file is considered stable if:
        1. It exists
        2. It's older than min_file_age_seconds
        3. Its size hasn't changed in the last second
        """
        try:
            if not path.exists():
                return False
            
            stat1 = path.stat()
            file_age = time.time() - stat1.st_mtime
            
            if file_age < self.min_file_age_seconds:
                return False
            
            # Double-check size hasn't changed
            time.sleep(0.1)
            stat2 = path.stat()
            
            return stat1.st_size == stat2.st_size
            
        except Exception as e:
            self.logger.warning(f"Error checking file stability for {path}: {e}")
            return False
    
    def _process_batch(self):
        """Process all pending files as a batch."""
        if not self.pending_files:
            return
        
        # Filter to stable files only
        stable_files = [f for f in self.pending_files if self._is_file_stable(f)]
        
        if not stable_files:
            self.logger.debug("No stable files ready for processing")
            self.pending_files.clear()
            return
        
        self.logger.info(f"Processing batch of {len(stable_files)} files")
        
        # Classify each file
        classifications = {}
        for file_path in stable_files:
            try:
                result = self.tax_classifier.classify(file_path)
                classifications[file_path] = result
                
                self.logger.info(
                    f"Classified {file_path.name}: "
                    f"year={result.inferred_year}, "
                    f"category={result.inferred_category}, "
                    f"confidence={result.confidence:.2f}"
                )
                
                # Log evidence
                for evidence in result.evidence:
                    self.logger.debug(f"  Evidence: {evidence}")
                    
            except Exception as e:
                self.logger.error(f"Error classifying {file_path}: {e}")
        
        # Generate sync plan for inbox files only
        try:
            plan = self.tax_sync.plan()
            
            # Filter plan to only include actions for our classified files
            inbox_files = {str(f.resolve()) for f in stable_files}
            
            # Categorize moves
            auto_apply_moves = []
            review_needed = []
            
            for src, dest in plan.to_move:
                src_path = Path(src).resolve()
                dest_path = Path(dest)
                
                if str(src_path) not in inbox_files:
                    continue
                
                # Check if destination is auto-approvable
                dest_str = str(dest_path)
                classification = classifications.get(src_path)
                
                if classification:
                    is_canonical = any(cat in dest_str for cat in [
                        '/taxes/', '/receipts/', '/bank_statements/',
                        '/insurance/', '/contracts/', '/healthcare/'
                    ])
                    is_misc = '_metadata/misc' in dest_str
                    is_duplicate = '_metadata/duplicates' in dest_str
                    
                    if (is_canonical and classification.confidence >= 0.7) or is_misc or is_duplicate:
                        auto_apply_moves.append((src, dest))
                    elif classification.confidence < 0.7:
                        # Low confidence - route to review
                        review_dest = self.root_path / "_metadata" / "review" / src_path.name
                        review_needed.append((src, str(review_dest), classification))
            
            # Apply automatic moves
            if auto_apply_moves:
                self.logger.info(f"Auto-applying {len(auto_apply_moves)} high-confidence moves")
                
                for src, dest in auto_apply_moves:
                    try:
                        src_path = Path(src)
                        dest_path = Path(dest)
                        
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        src_path.rename(dest_path)
                        
                        self.logger.info(f"Moved: {src_path.name} -> {dest_path.relative_to(self.root_path)}")
                        
                    except Exception as e:
                        self.logger.error(f"Error moving {src} to {dest}: {e}")
            
            # Handle review-needed files
            if review_needed:
                self.logger.warning(f"{len(review_needed)} files need manual review")
                
                for src, dest, classification in review_needed:
                    try:
                        src_path = Path(src)
                        dest_path = Path(dest)
                        
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        src_path.rename(dest_path)
                        
                        self.logger.warning(
                            f"Review needed: {src_path.name} "
                            f"(confidence={classification.confidence:.2f}, "
                            f"year={classification.inferred_year}, "
                            f"category={classification.inferred_category})"
                        )
                        
                    except Exception as e:
                        self.logger.error(f"Error moving {src} to review: {e}")
            
            # Handle duplicate moves from sync plan
            if plan.duplicate_moves:
                self.logger.info(f"Processing {len(plan.duplicate_moves)} duplicate resolutions")
                
                for src, dest in plan.duplicate_moves:
                    src_path = Path(src)
                    if src_path.resolve() in inbox_files:
                        try:
                            dest_path = Path(dest)
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            src_path.rename(dest_path)
                            self.logger.info(f"Duplicate resolved: {src_path.name}")
                        except Exception as e:
                            self.logger.error(f"Error resolving duplicate {src}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error during batch processing: {e}")
        
        finally:
            # Clear pending files
            self.pending_files.clear()
    
    def start(self):
        """
        Start watching the inbox directory.
        
        This method blocks until the watcher is stopped.
        """
        self.logger.info(f"Starting inbox watcher for {self.inbox_path}")
        
        # Create event handler
        event_handler = InboxEventHandler(self)
        
        # Create observer
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.inbox_path), recursive=False)
        self.observer.start()
        
        try:
            while True:
                time.sleep(1)
                
                # Check if debounce window has expired
                if self.pending_files and (time.time() - self.last_event_time) >= self.debounce_seconds:
                    self._process_batch()
                    
        except KeyboardInterrupt:
            self.logger.info("Stopping inbox watcher...")
            self.stop()
    
    def stop(self):
        """Stop watching the inbox directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.logger.info("Inbox watcher stopped")


class InboxEventHandler(FileSystemEventHandler):
    """Handles file system events for the inbox directory."""
    
    def __init__(self, watcher: TaxInboxWatcher):
        self.watcher = watcher
        super().__init__()
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        if self.watcher._is_ignored_file(file_path):
            return
        
        self.watcher.logger.debug(f"File created: {file_path.name}")
        self.watcher.pending_files.add(file_path)
        self.watcher.last_event_time = time.time()
    
    def on_moved(self, event):
        """Handle file move events (e.g., download completion)."""
        if event.is_directory:
            return
        
        file_path = Path(event.dest_path)
        
        if self.watcher._is_ignored_file(file_path):
            return
        
        self.watcher.logger.debug(f"File moved to inbox: {file_path.name}")
        self.watcher.pending_files.add(file_path)
        self.watcher.last_event_time = time.time()
