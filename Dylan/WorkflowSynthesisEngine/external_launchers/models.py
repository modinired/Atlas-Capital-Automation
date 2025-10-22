"""
Pydantic models for API request and response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ScriptParameterModel(BaseModel):
    """Script parameter specification."""
    name: str
    type: str
    description: str
    default: Optional[Any] = None
    required: bool = False
    choices: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class ScriptMetadataModel(BaseModel):
    """Script metadata for API responses."""
    id: str
    name: str
    path: str
    description: str
    parameters: List[ScriptParameterModel] = []
    tags: List[str] = []
    author: str = ""
    version: str = "1.0.0"
    python_version: str = "3.11"
    dependencies: List[str] = []
    timeout: Optional[int] = None
    working_directory: Optional[str] = None
    environment_variables: Dict[str, str] = {}
    created_at: str
    updated_at: str
    last_run: Optional[str] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    enabled: bool = True


class RegisterScriptRequest(BaseModel):
    """Request to register a new script."""
    name: str = Field(..., description="Script name")
    path: str = Field(..., description="Absolute path to the script file")
    description: str = Field(..., description="Script description")
    parameters: List[ScriptParameterModel] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    author: str = ""
    version: str = "1.0.0"
    timeout: Optional[int] = None
    working_directory: Optional[str] = None
    environment_variables: Dict[str, str] = Field(default_factory=dict)


class RegisterScriptResponse(BaseModel):
    """Response after registering a script."""
    success: bool
    script_id: Optional[str] = None
    message: str


class LaunchScriptRequest(BaseModel):
    """Request to launch a script."""
    script_id: str = Field(..., description="ID of the script to launch")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameter values")
    async_mode: bool = Field(default=False, description="Execute in background")


class ExecutionMetricsModel(BaseModel):
    """Execution metrics."""
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    cpu_percent: List[float] = []
    memory_mb: List[float] = []
    peak_memory_mb: float = 0.0
    exit_code: Optional[int] = None


class ExecutionResultModel(BaseModel):
    """Execution result."""
    status: str
    exit_code: Optional[int]
    stdout: str
    stderr: str
    metrics: Optional[ExecutionMetricsModel] = None
    error_message: Optional[str] = None


class LaunchScriptResponse(BaseModel):
    """Response after launching a script."""
    success: bool
    result: Optional[ExecutionResultModel] = None
    execution_id: Optional[str] = None
    message: str


class QuickLaunchRequest(BaseModel):
    """Request to quick launch a script without registration."""
    script_path: str = Field(..., description="Path to the script file")
    args: List[str] = Field(default_factory=list, description="Command-line arguments")


class ScriptListResponse(BaseModel):
    """Response with list of scripts."""
    scripts: List[ScriptMetadataModel]
    total: int


class ExecutionHistoryItem(BaseModel):
    """Single execution history item."""
    script_id: str
    script_name: str
    parameters: Dict[str, Any]
    status: str
    exit_code: Optional[int]
    duration: Optional[float]
    timestamp: str


class ExecutionHistoryResponse(BaseModel):
    """Response with execution history."""
    history: List[ExecutionHistoryItem]
    total: int


class StatusResponse(BaseModel):
    """API status response."""
    status: str
    version: str
    total_scripts: int
    active_executions: int
    uptime: float


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None


class ParameterPresetRequest(BaseModel):
    """Request to save parameter preset."""
    preset_name: str
    script_id: str
    values: Dict[str, Any]


class ParameterPresetResponse(BaseModel):
    """Response for parameter preset operations."""
    success: bool
    message: str
    presets: Optional[List[str]] = None


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str  # 'output', 'status', 'error', 'complete'
    stream: Optional[str] = None  # 'stdout' or 'stderr'
    data: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

