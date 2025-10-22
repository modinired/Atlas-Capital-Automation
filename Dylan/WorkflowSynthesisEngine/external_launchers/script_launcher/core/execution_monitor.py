"""
Execution monitor for real-time process tracking, output streaming, and status management.
"""

import subprocess
import threading
import queue
import time
import psutil
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from .logger import get_logger

logger = get_logger(__name__)


class ExecutionStatus(Enum):
    """Execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutionMetrics:
    """Metrics collected during script execution."""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    cpu_percent: List[float] = field(default_factory=list)
    memory_mb: List[float] = field(default_factory=list)
    peak_memory_mb: float = 0.0
    exit_code: Optional[int] = None
    
    def finalize(self):
        """Finalize metrics after execution."""
        if self.end_time is None:
            self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        if self.memory_mb:
            self.peak_memory_mb = max(self.memory_mb)


@dataclass
class ExecutionResult:
    """Complete execution result with output and metrics."""
    status: ExecutionStatus
    exit_code: Optional[int]
    stdout: str
    stderr: str
    metrics: ExecutionMetrics
    error_message: Optional[str] = None
    
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.COMPLETED and self.exit_code == 0


class OutputStreamHandler:
    """Handles real-time output streaming from subprocess."""
    
    def __init__(self, process: subprocess.Popen):
        self.process = process
        self.stdout_lines: List[str] = []
        self.stderr_lines: List[str] = []
        self.output_queue = queue.Queue()
        self.callbacks: List[Callable[[str, str], None]] = []
        self._stop_event = threading.Event()
        
        # Start output reader threads
        self.stdout_thread = threading.Thread(
            target=self._read_stream,
            args=(process.stdout, 'stdout'),
            daemon=True
        )
        self.stderr_thread = threading.Thread(
            target=self._read_stream,
            args=(process.stderr, 'stderr'),
            daemon=True
        )
        
        self.stdout_thread.start()
        self.stderr_thread.start()
    
    def _read_stream(self, stream, stream_name: str):
        """Read from a stream and queue output."""
        try:
            for line in iter(stream.readline, ''):
                if self._stop_event.is_set():
                    break
                
                line = line.rstrip('\n\r')
                if not line:
                    continue
                
                # Store line
                if stream_name == 'stdout':
                    self.stdout_lines.append(line)
                else:
                    self.stderr_lines.append(line)
                
                # Queue for real-time processing
                self.output_queue.put((stream_name, line))
                
                # Call callbacks
                for callback in self.callbacks:
                    try:
                        callback(stream_name, line)
                    except Exception as e:
                        logger.error(f"Output callback error: {e}")
        
        except Exception as e:
            logger.error(f"Error reading {stream_name}: {e}")
    
    def add_callback(self, callback: Callable[[str, str], None]):
        """Add a callback for real-time output."""
        self.callbacks.append(callback)
    
    def get_output(self, timeout: float = 0.1) -> Optional[tuple]:
        """Get next output line from queue."""
        try:
            return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def stop(self):
        """Stop reading output."""
        self._stop_event.set()
    
    def get_full_output(self) -> tuple:
        """Get complete stdout and stderr."""
        return '\n'.join(self.stdout_lines), '\n'.join(self.stderr_lines)


class ProcessMonitor:
    """Monitors process resource usage."""
    
    def __init__(self, pid: int, interval: float = 0.5):
        self.pid = pid
        self.interval = interval
        self.metrics = ExecutionMetrics()
        self._stop_event = threading.Event()
        self._thread = None
    
    def start(self):
        """Start monitoring."""
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()
    
    def _monitor(self):
        """Monitor process metrics."""
        try:
            process = psutil.Process(self.pid)
            
            while not self._stop_event.is_set():
                try:
                    # CPU usage
                    cpu = process.cpu_percent(interval=0.1)
                    self.metrics.cpu_percent.append(cpu)
                    
                    # Memory usage
                    mem = process.memory_info().rss / (1024 * 1024)  # MB
                    self.metrics.memory_mb.append(mem)
                    
                    time.sleep(self.interval)
                
                except psutil.NoSuchProcess:
                    break
                except Exception as e:
                    logger.error(f"Error monitoring process: {e}")
                    break
        
        except psutil.NoSuchProcess:
            logger.warning(f"Process {self.pid} not found")
    
    def stop(self):
        """Stop monitoring."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        self.metrics.finalize()


class ScriptExecutor:
    """Executes Python scripts with monitoring and output streaming."""
    
    def __init__(
        self,
        script_path: str,
        args: List[str] = None,
        env: Dict[str, str] = None,
        working_dir: Optional[str] = None,
        timeout: Optional[int] = None,
        python_executable: str = "python3"
    ):
        self.script_path = script_path
        self.args = args or []
        self.env = env
        self.working_dir = working_dir
        self.timeout = timeout
        self.python_executable = python_executable
        
        self.process: Optional[subprocess.Popen] = None
        self.output_handler: Optional[OutputStreamHandler] = None
        self.monitor: Optional[ProcessMonitor] = None
        self.status = ExecutionStatus.PENDING
    
    def execute(self, output_callback: Optional[Callable[[str, str], None]] = None) -> ExecutionResult:
        """
        Execute the script with monitoring.
        
        Args:
            output_callback: Optional callback for real-time output (stream_name, line)
            
        Returns:
            ExecutionResult with complete execution information
        """
        logger.info(f"Executing script: {self.script_path}")
        
        # Build command
        cmd = [self.python_executable, self.script_path] + self.args
        
        # Prepare environment
        import os
        env = os.environ.copy()
        if self.env:
            env.update(self.env)
        
        try:
            # Start process
            self.status = ExecutionStatus.RUNNING
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env,
                cwd=self.working_dir
            )
            
            # Start output handler
            self.output_handler = OutputStreamHandler(self.process)
            if output_callback:
                self.output_handler.add_callback(output_callback)
            
            # Start process monitor
            self.monitor = ProcessMonitor(self.process.pid)
            self.monitor.start()
            
            # Wait for completion
            try:
                exit_code = self.process.wait(timeout=self.timeout)
                
                # Give output threads time to finish
                time.sleep(0.5)
                
                if exit_code == 0:
                    self.status = ExecutionStatus.COMPLETED
                else:
                    self.status = ExecutionStatus.FAILED
                
            except subprocess.TimeoutExpired:
                logger.warning(f"Script execution timeout: {self.script_path}")
                self.process.kill()
                self.process.wait()
                self.status = ExecutionStatus.TIMEOUT
                exit_code = -1
            
            # Stop monitoring
            if self.monitor:
                self.monitor.stop()
            
            if self.output_handler:
                self.output_handler.stop()
            
            # Collect output
            stdout, stderr = self.output_handler.get_full_output()
            
            # Create result
            result = ExecutionResult(
                status=self.status,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                metrics=self.monitor.metrics if self.monitor else ExecutionMetrics()
            )
            
            logger.info(
                f"Script execution completed: {self.script_path} "
                f"(status={self.status.value}, exit_code={exit_code}, "
                f"duration={result.metrics.duration:.2f}s)"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Script execution error: {e}")
            self.status = ExecutionStatus.FAILED
            
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                exit_code=-1,
                stdout="",
                stderr="",
                metrics=ExecutionMetrics(),
                error_message=str(e)
            )
    
    def cancel(self):
        """Cancel running execution."""
        if self.process and self.process.poll() is None:
            logger.info(f"Cancelling script execution: {self.script_path}")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            
            self.status = ExecutionStatus.CANCELLED
            
            if self.monitor:
                self.monitor.stop()
            
            if self.output_handler:
                self.output_handler.stop()

