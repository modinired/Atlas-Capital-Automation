# API Guide

This document provides detailed information on how to use the Script Launcher Pro REST API. The API is designed for programmatic access, making it ideal for integration with coding agents and automation workflows.

## Base URL

By default, the API is available at `http://localhost:8000`.

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible on the local network.

## API Endpoints

### Scripts

#### `POST /scripts/register`

Register a new script.

**Request Body:**

```json
{
  "name": "My New Script",
  "path": "/path/to/my_script.py",
  "description": "This is a new script.",
  "parameters": [
    {
      "name": "input_file",
      "type": "file",
      "description": "Input file to process",
      "required": true
    }
  ],
  "tags": ["data", "processing"]
}
```

**Response:**

```json
{
  "success": true,
  "script_id": "a1b2c3d4e5f6",
  "message": "Script registered successfully: My New Script"
}
```

#### `GET /scripts`

List all registered scripts.

**Query Parameters:**

*   `enabled_only` (bool, optional): If true, returns only enabled scripts.
*   `tag` (string, optional): Filter scripts by a specific tag.

**Response:**

```json
{
  "scripts": [
    {
      "id": "a1b2c3d4e5f6",
      "name": "My New Script",
      ...
    }
  ],
  "total": 1
}
```

### Launching

#### `POST /launch`

Launch a registered script.

**Request Body:**

```json
{
  "script_id": "a1b2c3d4e5f6",
  "parameters": {
    "input_file": "/path/to/data.csv"
  },
  "async_mode": false
}
```

**Response:**

```json
{
  "success": true,
  "result": {
    "status": "completed",
    "exit_code": 0,
    "stdout": "Processing complete.",
    "stderr": "",
    ...
  },
  "message": "Script launched successfully"
}
```

#### `POST /quick-launch`

Launch a script without registration.

**Request Body:**

```json
{
  "script_path": "/path/to/temp_script.py",
  "args": ["--verbose"]
}
```

### History

#### `GET /history`

Get the execution history.

**Query Parameters:**

*   `limit` (int, optional): Number of history entries to return (default: 100).

**Response:**

```json
{
  "history": [
    {
      "script_id": "a1b2c3d4e5f6",
      "script_name": "My New Script",
      "status": "completed",
      ...
    }
  ],
  "total": 1
}
```

## WebSocket for Real-time Output

The API provides a WebSocket endpoint for real-time output streaming during script execution.

**Endpoint**: `ws://localhost:8000/ws/{execution_id}`

To use the WebSocket, you must first launch a script in `async_mode` to get an `execution_id`. Then, connect to the WebSocket endpoint with that ID.

**Message Format:**

The server will send messages in JSON format:

```json
{
  "type": "output",
  "stream": "stdout",
  "data": "This is a line of output.",
  "timestamp": "2025-10-21T10:00:00.123456"
}
```

