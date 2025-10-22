"""
Scheduler for automated script execution using APScheduler.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
import json
from pathlib import Path

from .launcher_engine import get_engine
from .script_registry import get_registry
from .logger import get_logger

logger = get_logger(__name__)


class ScriptScheduler:
    """
    Scheduler for automated script execution.
    Thread-safe singleton implementation.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.engine = get_engine()
        self.registry = get_registry()
        self.scheduler = BackgroundScheduler()
        self.scheduled_jobs: Dict[str, Dict[str, Any]] = {}
        
        self.config_dir = Path.home() / 'script_launcher' / 'config'
        self.schedule_file = self.config_dir / 'schedules.json'
        
        self._load_schedules()
        self.scheduler.start()
        
        logger.info("Scheduler initialized")
    
    def _load_schedules(self):
        """Load saved schedules from disk."""
        if self.schedule_file.exists():
            try:
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for job_id, job_data in data.items():
                    try:
                        self._restore_job(job_id, job_data)
                    except Exception as e:
                        logger.error(f"Failed to restore job {job_id}: {e}")
                
                logger.info(f"Loaded {len(self.scheduled_jobs)} scheduled jobs")
            except Exception as e:
                logger.error(f"Failed to load schedules: {e}")
    
    def _save_schedules(self):
        """Save schedules to disk."""
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_jobs, f, indent=2, ensure_ascii=False)
            logger.debug("Schedules saved")
        except Exception as e:
            logger.error(f"Failed to save schedules: {e}")
    
    def _restore_job(self, job_id: str, job_data: Dict[str, Any]):
        """Restore a job from saved data."""
        trigger_type = job_data['trigger_type']
        trigger_args = job_data['trigger_args']
        
        if trigger_type == 'cron':
            trigger = CronTrigger(**trigger_args)
        elif trigger_type == 'interval':
            trigger = IntervalTrigger(**trigger_args)
        elif trigger_type == 'date':
            trigger = DateTrigger(**trigger_args)
        else:
            logger.error(f"Unknown trigger type: {trigger_type}")
            return
        
        self.scheduler.add_job(
            func=self._execute_scheduled_script,
            trigger=trigger,
            id=job_id,
            args=[job_data['script_id'], job_data['parameters']],
            name=job_data['name']
        )
        
        self.scheduled_jobs[job_id] = job_data
        logger.info(f"Restored scheduled job: {job_data['name']}")
    
    def schedule_cron(
        self,
        job_id: str,
        name: str,
        script_id: str,
        parameters: Dict[str, Any],
        cron_expression: str
    ) -> bool:
        """
        Schedule a script using cron expression.
        
        Args:
            job_id: Unique job identifier
            name: Human-readable job name
            script_id: Script to execute
            parameters: Script parameters
            cron_expression: Cron expression (minute hour day month day_of_week)
            
        Returns:
            True if scheduled successfully
        """
        try:
            # Parse cron expression
            parts = cron_expression.split()
            if len(parts) != 5:
                logger.error("Cron expression must have 5 parts")
                return False
            
            minute, hour, day, month, day_of_week = parts
            
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
            
            # Add job
            self.scheduler.add_job(
                func=self._execute_scheduled_script,
                trigger=trigger,
                id=job_id,
                args=[script_id, parameters],
                name=name,
                replace_existing=True
            )
            
            # Save job data
            self.scheduled_jobs[job_id] = {
                'job_id': job_id,
                'name': name,
                'script_id': script_id,
                'parameters': parameters,
                'trigger_type': 'cron',
                'trigger_args': {
                    'minute': minute,
                    'hour': hour,
                    'day': day,
                    'month': month,
                    'day_of_week': day_of_week
                },
                'created_at': datetime.now().isoformat()
            }
            
            self._save_schedules()
            logger.info(f"Scheduled job: {name} with cron: {cron_expression}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule job: {e}")
            return False
    
    def schedule_interval(
        self,
        job_id: str,
        name: str,
        script_id: str,
        parameters: Dict[str, Any],
        seconds: Optional[int] = None,
        minutes: Optional[int] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None
    ) -> bool:
        """
        Schedule a script at regular intervals.
        
        Args:
            job_id: Unique job identifier
            name: Human-readable job name
            script_id: Script to execute
            parameters: Script parameters
            seconds, minutes, hours, days: Interval components
            
        Returns:
            True if scheduled successfully
        """
        try:
            trigger_args = {}
            if seconds:
                trigger_args['seconds'] = seconds
            if minutes:
                trigger_args['minutes'] = minutes
            if hours:
                trigger_args['hours'] = hours
            if days:
                trigger_args['days'] = days
            
            if not trigger_args:
                logger.error("At least one interval component must be specified")
                return False
            
            trigger = IntervalTrigger(**trigger_args)
            
            # Add job
            self.scheduler.add_job(
                func=self._execute_scheduled_script,
                trigger=trigger,
                id=job_id,
                args=[script_id, parameters],
                name=name,
                replace_existing=True
            )
            
            # Save job data
            self.scheduled_jobs[job_id] = {
                'job_id': job_id,
                'name': name,
                'script_id': script_id,
                'parameters': parameters,
                'trigger_type': 'interval',
                'trigger_args': trigger_args,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_schedules()
            logger.info(f"Scheduled job: {name} with interval: {trigger_args}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule job: {e}")
            return False
    
    def schedule_once(
        self,
        job_id: str,
        name: str,
        script_id: str,
        parameters: Dict[str, Any],
        run_date: datetime
    ) -> bool:
        """
        Schedule a script to run once at a specific time.
        
        Args:
            job_id: Unique job identifier
            name: Human-readable job name
            script_id: Script to execute
            parameters: Script parameters
            run_date: When to run the script
            
        Returns:
            True if scheduled successfully
        """
        try:
            trigger = DateTrigger(run_date=run_date)
            
            # Add job
            self.scheduler.add_job(
                func=self._execute_scheduled_script,
                trigger=trigger,
                id=job_id,
                args=[script_id, parameters],
                name=name,
                replace_existing=True
            )
            
            # Save job data
            self.scheduled_jobs[job_id] = {
                'job_id': job_id,
                'name': name,
                'script_id': script_id,
                'parameters': parameters,
                'trigger_type': 'date',
                'trigger_args': {'run_date': run_date.isoformat()},
                'created_at': datetime.now().isoformat()
            }
            
            self._save_schedules()
            logger.info(f"Scheduled job: {name} for {run_date}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule job: {e}")
            return False
    
    def unschedule(self, job_id: str) -> bool:
        """
        Remove a scheduled job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if removed successfully
        """
        try:
            self.scheduler.remove_job(job_id)
            
            if job_id in self.scheduled_jobs:
                del self.scheduled_jobs[job_id]
                self._save_schedules()
            
            logger.info(f"Unscheduled job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unschedule job: {e}")
            return False
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled jobs."""
        jobs = []
        
        for job_id, job_data in self.scheduled_jobs.items():
            # Get next run time from scheduler
            job = self.scheduler.get_job(job_id)
            next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
            
            job_info = job_data.copy()
            job_info['next_run'] = next_run
            jobs.append(job_info)
        
        return jobs
    
    def _execute_scheduled_script(self, script_id: str, parameters: Dict[str, Any]):
        """Execute a scheduled script."""
        script = self.registry.get_script(script_id)
        if not script:
            logger.error(f"Scheduled script not found: {script_id}")
            return
        
        logger.info(f"Executing scheduled script: {script.name}")
        
        try:
            result = self.engine.launch_script(
                script_id=script_id,
                parameters=parameters,
                async_mode=False
            )
            
            if result.is_success():
                logger.info(f"Scheduled execution completed: {script.name}")
            else:
                logger.error(f"Scheduled execution failed: {script.name}")
                
        except Exception as e:
            logger.error(f"Error executing scheduled script: {e}")
    
    def shutdown(self):
        """Shutdown the scheduler."""
        logger.info("Shutting down scheduler")
        self.scheduler.shutdown()


# Global scheduler instance
_scheduler = ScriptScheduler()


def get_scheduler() -> ScriptScheduler:
    """Get the global scheduler instance."""
    return _scheduler

