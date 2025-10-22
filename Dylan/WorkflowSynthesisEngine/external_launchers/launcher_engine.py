"""
Main launcher engine that orchestrates script execution, monitoring, and management.
"""

from typing import Optional, Dict, Any, Callable, List
from pathlib import Path
import threading
from datetime import datetime

from .script_registry import ScriptMetadata, get_registry
from .parameter_manager import ParameterManager, ParameterValidationError
from .execution_monitor import ScriptExecutor, ExecutionResult, ExecutionStatus
from .logger import get_logger, get_script_logger

logger = get_logger(__name__)


class LauncherEngine:
    """
    Main engine for launching and managing Python scripts.
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
        
        self.registry = get_registry()
        self.parameter_manager = ParameterManager()
        self.active_executions: Dict[str, ScriptExecutor] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        logger.info("Launcher engine initialized")
    
    def launch_script(
        self,
        script_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        output_callback: Optional[Callable[[str, str], None]] = None,
        async_mode: bool = False
    ) -> ExecutionResult:
        """
        Launch a registered script with specified parameters.
        
        Args:
            script_id: ID of the script to launch
            parameters: Dictionary of parameter values
            output_callback: Optional callback for real-time output
            async_mode: If True, return immediately and execute in background
            
        Returns:
            ExecutionResult with execution details
        """
        # Get script metadata
        script = self.registry.get_script(script_id)
        if not script:
            logger.error(f"Script not found: {script_id}")
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                exit_code=-1,
                stdout="",
                stderr="",
                metrics=None,
                error_message=f"Script not found: {script_id}"
            )
        
        if not script.enabled:
            logger.error(f"Script is disabled: {script.name}")
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                exit_code=-1,
                stdout="",
                stderr="",
                metrics=None,
                error_message=f"Script is disabled: {script.name}"
            )
        
        # Validate script file exists
        script_path = Path(script.path)
        if not script_path.exists():
            logger.error(f"Script file not found: {script.path}")
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                exit_code=-1,
                stdout="",
                stderr="",
                metrics=None,
                error_message=f"Script file not found: {script.path}"
            )
        
        # Validate and prepare parameters
        parameters = parameters or {}
        try:
            validated_params = self.parameter_manager.validate_parameters(
                script.parameters,
                parameters
            )
        except ParameterValidationError as e:
            logger.error(f"Parameter validation failed: {e}")
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                exit_code=-1,
                stdout="",
                stderr="",
                metrics=None,
                error_message=f"Parameter validation failed: {e}"
            )
        
        # Build command arguments
        args = self.parameter_manager.build_command_args(
            script.parameters,
            validated_params,
            style='posix'
        )
        
        # Create script logger
        script_logger = get_script_logger(script.name)
        script_logger.info(f"Launching script: {script.name}")
        script_logger.info(f"Parameters: {validated_params}")
        script_logger.info(f"Command args: {args}")
        
        # Create executor
        executor = ScriptExecutor(
            script_path=str(script_path.absolute()),
            args=args,
            env=script.environment_variables,
            working_dir=script.working_directory,
            timeout=script.timeout,
            python_executable="python3"
        )
        
        # Wrap output callback to include logging
        def combined_callback(stream_name: str, line: str):
            script_logger.info(f"[{stream_name}] {line}")
            if output_callback:
                output_callback(stream_name, line)
        
        # Execute
        if async_mode:
            # Execute in background thread
            execution_id = f"{script_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_executions[execution_id] = executor
            
            def execute_async():
                result = executor.execute(output_callback=combined_callback)
                self._record_execution(script_id, script.name, validated_params, result)
                self.registry.update_script_stats(script_id, result.is_success())
                if execution_id in self.active_executions:
                    del self.active_executions[execution_id]
            
            thread = threading.Thread(target=execute_async, daemon=True)
            thread.start()
            
            logger.info(f"Script launched in background: {script.name} ({execution_id})")
            return ExecutionResult(
                status=ExecutionStatus.RUNNING,
                exit_code=None,
                stdout="",
                stderr="",
                metrics=None,
                error_message=None
            )
        else:
            # Execute synchronously
            result = executor.execute(output_callback=combined_callback)
            self._record_execution(script_id, script.name, validated_params, result)
            self.registry.update_script_stats(script_id, result.is_success())
            return result
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running execution.
        
        Args:
            execution_id: ID of the execution to cancel
            
        Returns:
            True if cancelled successfully
        """
        if execution_id in self.active_executions:
            executor = self.active_executions[execution_id]
            executor.cancel()
            logger.info(f"Cancelled execution: {execution_id}")
            return True
        return False
    
    def get_active_executions(self) -> List[str]:
        """Get list of active execution IDs."""
        return list(self.active_executions.keys())
    
    def _record_execution(
        self,
        script_id: str,
        script_name: str,
        parameters: Dict[str, Any],
        result: ExecutionResult
    ):
        """Record execution in history."""
        record = {
            'script_id': script_id,
            'script_name': script_name,
            'parameters': parameters,
            'status': result.status.value,
            'exit_code': result.exit_code,
            'duration': result.metrics.duration if result.metrics else None,
            'timestamp': datetime.now().isoformat()
        }
        
        self.execution_history.append(record)
        
        # Keep only last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent execution history."""
        return self.execution_history[-limit:]
    
    def quick_launch(
        self,
        script_path: str,
        args: List[str] = None,
        output_callback: Optional[Callable[[str, str], None]] = None
    ) -> ExecutionResult:
        """
        Quick launch a script without registration.
        
        Args:
            script_path: Path to the script
            args: Command-line arguments
            output_callback: Optional callback for real-time output
            
        Returns:
            ExecutionResult
        """
        logger.info(f"Quick launching script: {script_path}")
        
        path = Path(script_path)
        if not path.exists():
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                exit_code=-1,
                stdout="",
                stderr="",
                metrics=None,
                error_message=f"Script file not found: {script_path}"
            )
        
        executor = ScriptExecutor(
            script_path=str(path.absolute()),
            args=args or [],
            python_executable="python3"
        )
        
        result = executor.execute(output_callback=output_callback)
        return result


# Global engine instance
_engine = LauncherEngine()


def get_engine() -> LauncherEngine:
    """Get the global launcher engine instance."""
    return _engine

