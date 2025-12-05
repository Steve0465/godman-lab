"""
Job worker that processes jobs from the queue.
"""
import time
import logging
import signal
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class JobWorker:
    """
    Worker that consumes jobs from JobQueue and processes them through AgentLoop.
    """
    
    def __init__(self, queue=None, episodic_memory=None):
        self.queue = queue
        self.episodic_memory = episodic_memory
        self.running = False
        self.agent_loop = None
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _get_queue(self):
        """Lazy-load job queue."""
        if self.queue is None:
            from godman_ai.queue.job_queue import JobQueue
            self.queue = JobQueue()
        return self.queue
    
    def _get_episodic_memory(self):
        """Lazy-load episodic memory."""
        if self.episodic_memory is None:
            from godman_ai.memory import EpisodicMemory
            self.episodic_memory = EpisodicMemory()
        return self.episodic_memory
    
    def _get_agent_loop(self):
        """Lazy-load agent loop."""
        if self.agent_loop is None:
            from godman_ai.agents.agent_loop import AgentLoop
            self.agent_loop = AgentLoop()
        return self.agent_loop
    
    def process_job(self, job: dict) -> dict:
        """
        Process a single job through the agent loop.
        
        Args:
            job: Job dict from queue
            
        Returns:
            Result dict
        """
        job_id = job['id']
        payload = job['payload']
        task_input = payload.get('task_input')
        
        logger.info(f"Processing job {job_id}: {task_input}")
        
        try:
            # Run through agent loop
            agent_loop = self._get_agent_loop()
            result = agent_loop.run(task_input)
            
            # Store in episodic memory
            episodic = self._get_episodic_memory()
            episodic.add_episode(
                task_input=task_input,
                plan=result.get('raw_plan', []),
                results=result,
                metadata={'job_id': job_id}
            )
            
            logger.info(f"Job {job_id} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            raise
    
    def run_forever(self, poll_interval: float = 2.0):
        """
        Run worker loop forever, processing jobs as they arrive.
        
        Args:
            poll_interval: Seconds to wait between queue checks
        """
        self.running = True
        queue = self._get_queue()
        
        logger.info(f"Worker started (poll interval: {poll_interval}s)")
        
        while self.running:
            try:
                # Try to get a job
                job = queue.dequeue()
                
                if job is None:
                    # No jobs available, wait
                    time.sleep(poll_interval)
                    continue
                
                job_id = job['id']
                
                try:
                    # Process the job
                    result = self.process_job(job)
                    queue.mark_complete(job_id)
                    
                except Exception as e:
                    # Mark as failed
                    error_msg = str(e)
                    queue.mark_complete(job_id, error=error_msg)
                    logger.error(f"Job {job_id} failed: {error_msg}")
                
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                time.sleep(poll_interval)
        
        logger.info("Worker stopped")
    
    def run_once(self) -> Optional[dict]:
        """
        Process one job from the queue and return.
        
        Returns:
            Job result or None if no jobs available
        """
        queue = self._get_queue()
        job = queue.dequeue()
        
        if job is None:
            return None
        
        job_id = job['id']
        
        try:
            result = self.process_job(job)
            queue.mark_complete(job_id)
            return result
        except Exception as e:
            error_msg = str(e)
            queue.mark_complete(job_id, error=error_msg)
            raise
