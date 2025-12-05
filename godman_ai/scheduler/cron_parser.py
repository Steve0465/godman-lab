"""
Cron expression parser with fallback to basic 5-field parsing.
"""
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CronParser:
    """
    Parse cron expressions and calculate next run time.
    Uses python-croniter if available, otherwise basic parser.
    """
    
    def __init__(self, cron_expr: str):
        self.cron_expr = cron_expr
        self._croniter = None
        self._use_croniter = True
        
        try:
            from croniter import croniter
            self._croniter = croniter(cron_expr, datetime.now())
        except ImportError:
            logger.warning("croniter not installed, using basic cron parser")
            self._use_croniter = False
        except Exception as e:
            logger.error(f"Invalid cron expression: {e}")
            self._use_croniter = False
    
    def get_next(self, base_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Get next run time based on cron expression.
        
        Args:
            base_time: Base time to calculate from (defaults to now)
            
        Returns:
            Next run datetime or None if invalid
        """
        if base_time is None:
            base_time = datetime.now()
        
        if self._use_croniter and self._croniter:
            try:
                return self._croniter.get_next(datetime)
            except Exception as e:
                logger.error(f"Error calculating next run: {e}")
                return None
        else:
            return self._basic_next(base_time)
    
    def _basic_next(self, base_time: datetime) -> Optional[datetime]:
        """
        Basic cron parser for simple expressions.
        Supports: minute hour day month weekday
        """
        parts = self.cron_expr.split()
        if len(parts) != 5:
            logger.error(f"Invalid cron expression (expected 5 fields): {self.cron_expr}")
            return None
        
        minute, hour, day, month, weekday = parts
        
        # For now, support only simple cases
        # Format: "*/N * * * *" (every N minutes)
        if minute.startswith("*/"):
            try:
                interval = int(minute[2:])
                next_time = base_time + timedelta(minutes=interval)
                return next_time.replace(second=0, microsecond=0)
            except ValueError:
                pass
        
        # Format: "M H * * *" (daily at specific time)
        if minute.isdigit() and hour.isdigit() and day == "*" and month == "*" and weekday == "*":
            try:
                target_hour = int(hour)
                target_minute = int(minute)
                next_time = base_time.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                
                if next_time <= base_time:
                    next_time += timedelta(days=1)
                
                return next_time
            except ValueError:
                pass
        
        logger.warning(f"Unsupported cron expression (use croniter for full support): {self.cron_expr}")
        return None
    
    def is_valid(self) -> bool:
        """Check if cron expression is valid."""
        return self.get_next() is not None


def parse_cron(cron_expr: str) -> CronParser:
    """
    Parse a cron expression.
    
    Args:
        cron_expr: Cron expression string
        
    Returns:
        CronParser instance
    """
    return CronParser(cron_expr)
