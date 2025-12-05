"""
Time-driven task scheduler with cron support.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ScheduleEntry:
    """A scheduled task entry."""
    id: int
    cron: str
    command: str
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    created_at: Optional[str] = None


class Scheduler:
    """
    Basic time-driven scheduler that enqueues jobs based on cron schedules.
    """
    
    def __init__(self, schedule_file: str = ".godman/state/schedules.json"):
        self.schedule_file = Path(schedule_file)
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.schedules: List[ScheduleEntry] = []
        self.next_id = 1
        self._load()
        self._update_next_runs()
    
    def _load(self):
        """Load schedules from disk."""
        if not self.schedule_file.exists():
            return
        
        try:
            with open(self.schedule_file, 'r') as f:
                data = json.load(f)
                self.schedules = [ScheduleEntry(**entry) for entry in data.get('schedules', [])]
                self.next_id = data.get('next_id', 1)
        except Exception as e:
            logger.error(f"Error loading schedules: {e}")
    
    def _save(self):
        """Save schedules to disk."""
        try:
            data = {
                'schedules': [asdict(s) for s in self.schedules],
                'next_id': self.next_id
            }
            with open(self.schedule_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving schedules: {e}")
    
    def _update_next_runs(self):
        """Update next_run time for all schedules."""
        from godman_ai.scheduler.cron_parser import parse_cron
        
        for schedule in self.schedules:
            if not schedule.enabled:
                continue
            
            try:
                parser = parse_cron(schedule.cron)
                next_run = parser.get_next()
                if next_run:
                    schedule.next_run = next_run.isoformat()
            except Exception as e:
                logger.error(f"Error updating schedule {schedule.id}: {e}")
    
    def add_schedule(self, cron: str, command: str, enabled: bool = True) -> int:
        """
        Add a new scheduled task.
        
        Args:
            cron: Cron expression
            command: Command to execute
            enabled: Whether schedule is enabled
            
        Returns:
            Schedule ID
        """
        from godman_ai.scheduler.cron_parser import parse_cron
        
        # Validate cron expression
        parser = parse_cron(cron)
        if not parser.is_valid():
            raise ValueError(f"Invalid cron expression: {cron}")
        
        schedule = ScheduleEntry(
            id=self.next_id,
            cron=cron,
            command=command,
            enabled=enabled,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Calculate next run
        next_run = parser.get_next()
        if next_run:
            schedule.next_run = next_run.isoformat()
        
        self.schedules.append(schedule)
        self.next_id += 1
        self._save()
        
        logger.info(f"Added schedule {schedule.id}: {cron} -> {command}")
        return schedule.id
    
    def remove_schedule(self, schedule_id: int) -> bool:
        """
        Remove a schedule by ID.
        
        Args:
            schedule_id: Schedule ID to remove
            
        Returns:
            True if removed, False if not found
        """
        original_len = len(self.schedules)
        self.schedules = [s for s in self.schedules if s.id != schedule_id]
        
        if len(self.schedules) < original_len:
            self._save()
            logger.info(f"Removed schedule {schedule_id}")
            return True
        
        return False
    
    def enable_schedule(self, schedule_id: int, enabled: bool = True):
        """Enable or disable a schedule."""
        for schedule in self.schedules:
            if schedule.id == schedule_id:
                schedule.enabled = enabled
                self._save()
                logger.info(f"Schedule {schedule_id} {'enabled' if enabled else 'disabled'}")
                return
        
        raise ValueError(f"Schedule {schedule_id} not found")
    
    def get_schedules(self) -> List[ScheduleEntry]:
        """Get all schedules."""
        return self.schedules.copy()
    
    def run_pending(self, queue=None):
        """
        Check for pending scheduled tasks and enqueue them.
        
        Args:
            queue: JobQueue instance (lazy-loaded if not provided)
        """
        if queue is None:
            from godman_ai.queue import JobQueue
            queue = JobQueue()
        
        from godman_ai.scheduler.cron_parser import parse_cron
        
        now = datetime.utcnow()
        
        for schedule in self.schedules:
            if not schedule.enabled:
                continue
            
            if not schedule.next_run:
                continue
            
            next_run = datetime.fromisoformat(schedule.next_run)
            
            if now >= next_run:
                # Time to run this schedule
                logger.info(f"Triggering schedule {schedule.id}: {schedule.command}")
                
                try:
                    # Enqueue the command
                    queue.enqueue(schedule.command, priority=5)
                    
                    # Update last_run and next_run
                    schedule.last_run = now.isoformat()
                    parser = parse_cron(schedule.cron)
                    next_run_time = parser.get_next(now)
                    if next_run_time:
                        schedule.next_run = next_run_time.isoformat()
                    
                except Exception as e:
                    logger.error(f"Error running schedule {schedule.id}: {e}")
        
        self._save()
    
    def clear(self):
        """Clear all schedules."""
        self.schedules = []
        self.next_id = 1
        self._save()
