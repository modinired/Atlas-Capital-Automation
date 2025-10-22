"""
FastAPI-based REST API for coding agent access to the script launcher.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import time
import asyncio
from datetime import datetime

from .models import (
    RegisterScriptRequest, RegisterScriptResponse,
    LaunchScriptRequest, LaunchScriptResponse,
    QuickLaunchRequest, ExecutionResultModel, ExecutionMetricsModel,
    ScriptListResponse, ScriptMetadataModel, ScriptParameterModel,
    ExecutionHistoryResponse, ExecutionHistoryItem,
    StatusResponse, ErrorResponse,
    ParameterPresetRequest, ParameterPresetResponse,
    WebSocketMessage
)

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.launcher_engine import get_engine
from core.script_registry import ScriptMetadata, ScriptParameter, get_registry
from core.parameter_manager import ParameterManager
from core.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Script Launcher API",
    description="Production-ready API for launching and managing Python scripts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
engine = get_engine()
registry = get_registry()
param_manager = ParameterManager()
start_time = time.time()

# WebSocket connections
websocket_connections: List[WebSocket] = []


@app.get("/", response_model=StatusResponse)
async def root():
    """API status and information."""
    return StatusResponse(
        status="running",
        version="1.0.0",
        total_scripts=len(registry.get_all_scripts()),
        active_executions=len(engine.get_active_executions()),
        uptime=time.time() - start_time
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/scripts/register", response_model=RegisterScriptResponse)
async def register_script(request: RegisterScriptRequest):
    """Register a new script."""
    try:
        # Convert request to ScriptMetadata
        parameters = [
            ScriptParameter(
                name=p.name,
                type=p.type,
                description=p.description,
                default=p.default,
                required=p.required,
                choices=p.choices,
                min_value=p.min_value,
                max_value=p.max_value
            )
            for p in request.parameters
        ]
        
        metadata = ScriptMetadata(
            id="",  # Will be generated
            name=request.name,
            path=request.path,
            description=request.description,
            parameters=parameters,
            tags=request.tags,
            author=request.author,
            version=request.version,
            timeout=request.timeout,
            working_directory=request.working_directory,
            environment_variables=request.environment_variables
        )
        
        script_id = registry.register_script(metadata)
        
        return RegisterScriptResponse(
            success=True,
            script_id=script_id,
            message=f"Script registered successfully: {request.name}"
        )
    
    except Exception as e:
        logger.error(f"Failed to register script: {e}")
        return RegisterScriptResponse(
            success=False,
            message=f"Failed to register script: {str(e)}"
        )


@app.get("/scripts", response_model=ScriptListResponse)
async def list_scripts(enabled_only: bool = False, tag: Optional[str] = None):
    """List all registered scripts."""
    if tag:
        scripts = registry.get_scripts_by_tag(tag)
    elif enabled_only:
        scripts = registry.get_enabled_scripts()
    else:
        scripts = registry.get_all_scripts()
    
    # Convert to response models
    script_models = []
    for script in scripts:
        params = [
            ScriptParameterModel(
                name=p.name,
                type=p.type,
                description=p.description,
                default=p.default,
                required=p.required,
                choices=p.choices,
                min_value=p.min_value,
                max_value=p.max_value
            )
            for p in script.parameters
        ]
        
        script_models.append(ScriptMetadataModel(
            id=script.id,
            name=script.name,
            path=script.path,
            description=script.description,
            parameters=params,
            tags=script.tags,
            author=script.author,
            version=script.version,
            python_version=script.python_version,
            dependencies=script.dependencies,
            timeout=script.timeout,
            working_directory=script.working_directory,
            environment_variables=script.environment_variables,
            created_at=script.created_at,
            updated_at=script.updated_at,
            last_run=script.last_run,
            run_count=script.run_count,
            success_count=script.success_count,
            failure_count=script.failure_count,
            enabled=script.enabled
        ))
    
    return ScriptListResponse(scripts=script_models, total=len(script_models))


@app.get("/scripts/{script_id}", response_model=ScriptMetadataModel)
async def get_script(script_id: str):
    """Get details of a specific script."""
    script = registry.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail=f"Script not found: {script_id}")
    
    params = [
        ScriptParameterModel(
            name=p.name,
            type=p.type,
            description=p.description,
            default=p.default,
            required=p.required,
            choices=p.choices,
            min_value=p.min_value,
            max_value=p.max_value
        )
        for p in script.parameters
    ]
    
    return ScriptMetadataModel(
        id=script.id,
        name=script.name,
        path=script.path,
        description=script.description,
        parameters=params,
        tags=script.tags,
        author=script.author,
        version=script.version,
        python_version=script.python_version,
        dependencies=script.dependencies,
        timeout=script.timeout,
        working_directory=script.working_directory,
        environment_variables=script.environment_variables,
        created_at=script.created_at,
        updated_at=script.updated_at,
        last_run=script.last_run,
        run_count=script.run_count,
        success_count=script.success_count,
        failure_count=script.failure_count,
        enabled=script.enabled
    )


@app.delete("/scripts/{script_id}")
async def unregister_script(script_id: str):
    """Unregister a script."""
    success = registry.unregister_script(script_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Script not found: {script_id}")
    
    return {"success": True, "message": f"Script unregistered: {script_id}"}


@app.post("/scripts/{script_id}/toggle")
async def toggle_script(script_id: str):
    """Enable or disable a script."""
    enabled = registry.toggle_script(script_id)
    if enabled is False and script_id not in registry.scripts:
        raise HTTPException(status_code=404, detail=f"Script not found: {script_id}")
    
    return {"success": True, "enabled": enabled}


@app.post("/launch", response_model=LaunchScriptResponse)
async def launch_script(request: LaunchScriptRequest):
    """Launch a registered script."""
    try:
        result = engine.launch_script(
            script_id=request.script_id,
            parameters=request.parameters,
            async_mode=request.async_mode
        )
        
        # Convert result to response model
        metrics_model = None
        if result.metrics:
            metrics_model = ExecutionMetricsModel(
                start_time=result.metrics.start_time,
                end_time=result.metrics.end_time,
                duration=result.metrics.duration,
                cpu_percent=result.metrics.cpu_percent,
                memory_mb=result.metrics.memory_mb,
                peak_memory_mb=result.metrics.peak_memory_mb,
                exit_code=result.metrics.exit_code
            )
        
        result_model = ExecutionResultModel(
            status=result.status.value,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            metrics=metrics_model,
            error_message=result.error_message
        )
        
        return LaunchScriptResponse(
            success=result.is_success(),
            result=result_model,
            message="Script launched successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to launch script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quick-launch", response_model=LaunchScriptResponse)
async def quick_launch(request: QuickLaunchRequest):
    """Quick launch a script without registration."""
    try:
        result = engine.quick_launch(
            script_path=request.script_path,
            args=request.args
        )
        
        metrics_model = None
        if result.metrics:
            metrics_model = ExecutionMetricsModel(
                start_time=result.metrics.start_time,
                end_time=result.metrics.end_time,
                duration=result.metrics.duration,
                cpu_percent=result.metrics.cpu_percent,
                memory_mb=result.metrics.memory_mb,
                peak_memory_mb=result.metrics.peak_memory_mb,
                exit_code=result.metrics.exit_code
            )
        
        result_model = ExecutionResultModel(
            status=result.status.value,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            metrics=metrics_model,
            error_message=result.error_message
        )
        
        return LaunchScriptResponse(
            success=result.is_success(),
            result=result_model,
            message="Script executed successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to quick launch script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history", response_model=ExecutionHistoryResponse)
async def get_history(limit: int = 100):
    """Get execution history."""
    history = engine.get_execution_history(limit=limit)
    
    items = [
        ExecutionHistoryItem(
            script_id=h['script_id'],
            script_name=h['script_name'],
            parameters=h['parameters'],
            status=h['status'],
            exit_code=h['exit_code'],
            duration=h['duration'],
            timestamp=h['timestamp']
        )
        for h in history
    ]
    
    return ExecutionHistoryResponse(history=items, total=len(items))


@app.get("/executions/active")
async def get_active_executions():
    """Get list of active executions."""
    active = engine.get_active_executions()
    return {"active_executions": active, "count": len(active)}


@app.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    """Cancel a running execution."""
    success = engine.cancel_execution(execution_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Execution not found: {execution_id}")
    
    return {"success": True, "message": f"Execution cancelled: {execution_id}"}


@app.post("/presets/save", response_model=ParameterPresetResponse)
async def save_preset(request: ParameterPresetRequest):
    """Save a parameter preset."""
    success = param_manager.save_parameter_preset(
        request.preset_name,
        request.script_id,
        request.values
    )
    
    return ParameterPresetResponse(
        success=success,
        message="Preset saved successfully" if success else "Failed to save preset"
    )


@app.get("/presets/{script_id}", response_model=ParameterPresetResponse)
async def list_presets(script_id: str):
    """List available presets for a script."""
    presets = param_manager.list_presets(script_id)
    return ParameterPresetResponse(
        success=True,
        message=f"Found {len(presets)} presets",
        presets=presets
    )


@app.get("/presets/{script_id}/{preset_name}")
async def load_preset(script_id: str, preset_name: str):
    """Load a parameter preset."""
    values = param_manager.load_parameter_preset(preset_name, script_id)
    if values is None:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    return {"success": True, "values": values}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

