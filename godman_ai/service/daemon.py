"""
Daemon mode for GodmanAI

Runs scheduler and queue worker as background processes.
"""

import logging
import multiprocessing
import time
import signal
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GodmanDaemon:
    """Background daemon for running scheduler and queue worker"""
    
    def __init__(self):
        self.pid_file = Path.home() / ".godman" / "daemon.pid"
        self.log_dir = Path.home() / ".godman" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.scheduler_process: Optional[multiprocessing.Process] = None
        self.worker_process: Optional[multiprocessing.Process] = None
    
    def _scheduler_loop(self):
        """Run the scheduler loop"""
        try:
            from godman_ai.scheduler.scheduler import Scheduler
            
            scheduler = Scheduler()
            logger.info("Scheduler loop started")
            
            while True:
                try:
                    scheduler.run_pending()
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                    time.sleep(5)
        except Exception as e:
            logger.error(f"Fatal error in scheduler loop: {e}", exc_info=True)
    
    def _worker_loop(self):
        """Run the queue worker loop"""
        try:
            from godman_ai.queue.job_worker import JobWorker
            
            worker = JobWorker()
            logger.info("Worker loop started")
            worker.run_forever(poll_interval=2.0)
        except Exception as e:
            logger.error(f"Fatal error in worker loop: {e}", exc_info=True)
    
    def start(self):
        """Start the daemon"""
        if self.is_running():
            print("❌ Daemon is already running")
            return False
        
        print("🚀 Starting GodmanAI daemon...")
        
        # Start scheduler process
        self.scheduler_process = multiprocessing.Process(
            target=self._scheduler_loop,
            name="godman-scheduler"
        )
        self.scheduler_process.daemon = True
        self.scheduler_process.start()
        
        # Start worker process
        self.worker_process = multiprocessing.Process(
            target=self._worker_loop,
            name="godman-worker"
        )
        self.worker_process.daemon = True
        self.worker_process.start()
        
        # Write PID file
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.pid_file, "w") as f:
            f.write(f"{self.scheduler_process.pid}\n{self.worker_process.pid}")
        
        print(f"✅ Daemon started (scheduler PID: {self.scheduler_process.pid}, worker PID: {self.worker_process.pid})")
        print(f"📁 Logs: {self.log_dir}")
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            print("\n🛑 Stopping daemon...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Keep alive
        try:
            while True:
                if self.scheduler_process and not self.scheduler_process.is_alive():
                    logger.warning("Scheduler process died, restarting...")
                    self.scheduler_process = multiprocessing.Process(
                        target=self._scheduler_loop,
                        name="godman-scheduler"
                    )
                    self.scheduler_process.daemon = True
                    self.scheduler_process.start()
                
                if self.worker_process and not self.worker_process.is_alive():
                    logger.warning("Worker process died, restarting...")
                    self.worker_process = multiprocessing.Process(
                        target=self._worker_loop,
                        name="godman-worker"
                    )
                    self.worker_process.daemon = True
                    self.worker_process.start()
                
                time.sleep(5)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the daemon"""
        if not self.is_running():
            print("❌ Daemon is not running")
            return False
        
        print("🛑 Stopping GodmanAI daemon...")
        
        # Terminate processes
        if self.scheduler_process and self.scheduler_process.is_alive():
            self.scheduler_process.terminate()
            self.scheduler_process.join(timeout=5)
        
        if self.worker_process and self.worker_process.is_alive():
            self.worker_process.terminate()
            self.worker_process.join(timeout=5)
        
        # Remove PID file
        if self.pid_file.exists():
            self.pid_file.unlink()
        
        print("✅ Daemon stopped")
        return True
    
    def is_running(self) -> bool:
        """Check if daemon is running"""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file) as f:
                pids = [int(line.strip()) for line in f if line.strip()]
            
            # Check if processes are alive (basic check without psutil)
            import os
            for pid in pids:
                try:
                    os.kill(pid, 0)  # Send signal 0 to check if process exists
                    return True
                except OSError:
                    continue
            
            # PID file exists but no processes running
            self.pid_file.unlink()
            return False
        except Exception:
            return False
    
    def status(self) -> dict:
        """Get daemon status"""
        if not self.is_running():
            return {
                "running": False,
                "message": "Daemon is not running"
            }
        
        status = {
            "running": True,
            "scheduler": {
                "pid": self.scheduler_process.pid if self.scheduler_process else None,
                "alive": self.scheduler_process.is_alive() if self.scheduler_process else False
            },
            "worker": {
                "pid": self.worker_process.pid if self.worker_process else None,
                "alive": self.worker_process.is_alive() if self.worker_process else False
            }
        }
        
        return status
