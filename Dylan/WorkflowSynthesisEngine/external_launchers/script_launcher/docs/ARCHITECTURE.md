# Script Launcher Architecture

## Overview
A production-ready Python script launcher with GUI, CLI, and API interfaces designed for macOS with cross-platform compatibility.

## Core Components

### 1. Core Engine (`core/`)
- **launcher_engine.py**: Main execution engine with process management
- **script_registry.py**: Script registration and metadata management
- **parameter_manager.py**: Dynamic parameter configuration and validation
- **execution_monitor.py**: Real-time process monitoring and status tracking
- **logger.py**: Comprehensive logging system with rotation

### 2. API Layer (`api/`)
- **rest_api.py**: FastAPI-based REST endpoints for coding agents
- **websocket_server.py**: WebSocket for real-time output streaming
- **models.py**: Pydantic models for request/response validation

### 3. GUI Interface (`gui/`)
- **main_window.py**: CustomTkinter main application window
- **script_panel.py**: Script selection and management panel
- **parameter_panel.py**: Dynamic parameter input forms
- **terminal_widget.py**: Live terminal output with ANSI color support
- **monitor_panel.py**: Process monitoring dashboard

### 4. CLI Interface (`cli/`)
- **cli_main.py**: Click-based command-line interface
- **interactive_mode.py**: Interactive terminal UI with Rich
- **live_monitor.py**: Real-time output streaming in terminal

### 5. Configuration (`config/`)
- **settings.py**: Application settings and defaults
- **script_configs/**: JSON-based script configurations

## Design Patterns

- **Singleton**: Logger and configuration manager
- **Observer**: Real-time output monitoring
- **Factory**: Script executor creation
- **Strategy**: Different execution modes (sync, async, scheduled)
- **Command**: Script execution encapsulation

## Data Flow

1. User/Agent → Interface (GUI/CLI/API)
2. Interface → Core Engine
3. Core Engine → Script Executor
4. Script Executor → Process Monitor
5. Process Monitor → Output Streams (Terminal/Log/WebSocket)

## Key Features

- ✓ Multi-interface access (GUI, CLI, API)
- ✓ Real-time output streaming
- ✓ Parameter validation and persistence
- ✓ Process monitoring and control
- ✓ Scheduling support
- ✓ Comprehensive logging
- ✓ Agent-friendly JSON API
- ✓ macOS-optimized UI

