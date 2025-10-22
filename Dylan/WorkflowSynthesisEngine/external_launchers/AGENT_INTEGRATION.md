# Agent Integration Guide

This guide explains how coding agents and automation tools can integrate with Script Launcher Pro.

## Overview

Script Launcher Pro provides multiple interfaces for agent access:

1.  **REST API**: JSON-based HTTP endpoints for all operations
2.  **CLI with JSON output**: Command-line interface with machine-readable output
3.  **Python module imports**: Direct integration by importing the core modules

## REST API Integration

The REST API is the recommended method for agent integration.

### Starting the API Server

```bash
python3 main.py api
```

The API will be available at `http://localhost:8000`.

### Key Endpoints for Agents

#### 1. List Available Scripts

```bash
GET /scripts?format=json
```

Returns a JSON array of all registered scripts with their metadata.

#### 2. Get Script Details

```bash
GET /scripts/{script_id}
```

Returns detailed information about a specific script, including its parameters.

#### 3. Launch a Script

```bash
POST /launch
Content-Type: application/json

{
  "script_id": "abc123",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  },
  "async_mode": false
}
```

Returns the execution result, including stdout, stderr, exit code, and metrics.

#### 4. Quick Launch (No Registration)

```bash
POST /quick-launch
Content-Type: application/json

{
  "script_path": "/path/to/script.py",
  "args": ["--arg1", "value1"]
}
```

Useful for one-off script executions without registration.

#### 5. View Execution History

```bash
GET /history?limit=50
```

Returns the execution history for monitoring and analysis.

### Example: Python Agent Integration

```python
import requests

API_BASE = "http://localhost:8000"

class ScriptLauncherAgent:
    def __init__(self, base_url=API_BASE):
        self.base_url = base_url
    
    def list_scripts(self):
        response = requests.get(f"{self.base_url}/scripts")
        return response.json()
    
    def get_script(self, script_id):
        response = requests.get(f"{self.base_url}/scripts/{script_id}")
        return response.json()
    
    def launch_script(self, script_id, parameters=None):
        payload = {
            "script_id": script_id,
            "parameters": parameters or {},
            "async_mode": False
        }
        response = requests.post(f"{self.base_url}/launch", json=payload)
        return response.json()
    
    def quick_launch(self, script_path, args=None):
        payload = {
            "script_path": script_path,
            "args": args or []
        }
        response = requests.post(f"{self.base_url}/quick-launch", json=payload)
        return response.json()

# Usage
agent = ScriptLauncherAgent()

# List all scripts
scripts = agent.list_scripts()
print(f"Found {scripts['total']} scripts")

# Launch a script
result = agent.launch_script("abc123", {"input_file": "/data/input.csv"})
if result['success']:
    print(f"Exit code: {result['result']['exit_code']}")
    print(f"Output: {result['result']['stdout']}")
```

## CLI Integration

For agents that prefer command-line interaction, the CLI provides JSON output:

```bash
# List scripts in JSON format
python3 main.py list --format json

# Get script info in JSON format
python3 main.py info <script_id> --format json

# View history in JSON format
python3 main.py history --format json
```

### Example: Shell Script Integration

```bash
#!/bin/bash

# Get list of scripts
SCRIPTS=$(python3 main.py list --format json)

# Parse with jq and launch first script
SCRIPT_ID=$(echo "$SCRIPTS" | jq -r '.[0].id')
python3 main.py launch "$SCRIPT_ID" --param input=/data/file.txt
```

## Direct Python Module Integration

For maximum control, agents can directly import and use the core modules:

```python
from core import get_engine, get_registry

# Get instances
engine = get_engine()
registry = get_registry()

# List scripts
scripts = registry.get_all_scripts()
for script in scripts:
    print(f"{script.id}: {script.name}")

# Launch a script
result = engine.launch_script(
    script_id="abc123",
    parameters={"input_file": "/data/input.csv"}
)

print(f"Exit code: {result.exit_code}")
print(f"Output: {result.stdout}")
```

## Best Practices for Agents

1.  **Use the REST API** for most integrations - it provides the best isolation and stability.
2.  **Check script status** before launching - use `GET /scripts/{id}` to verify the script is enabled.
3.  **Handle errors gracefully** - check the `success` field in API responses.
4.  **Use async mode for long-running scripts** - set `async_mode: true` to avoid timeouts.
5.  **Monitor execution history** - use `GET /history` to track script performance over time.
6.  **Validate parameters** - the API will return validation errors if parameters are incorrect.

## Error Handling

All API endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "detail": "Detailed error message"
}
```

HTTP status codes:

*   `200`: Success
*   `400`: Bad request (invalid parameters)
*   `404`: Resource not found
*   `500`: Internal server error

## Rate Limiting

Currently, there is no rate limiting on the API. However, for production deployments, consider implementing rate limiting to prevent abuse.

