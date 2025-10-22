# Quick Start Guide

Welcome to Script Launcher Pro! This guide will help you get started quickly.

## Installation

### Step 1: Install Dependencies

```bash
pip3 install -r requirements.txt
```

### Step 2: Verify Installation

Run the test suite to ensure everything is working correctly:

```bash
python3 tests/test_core.py
```

You should see output indicating that all tests passed.

## Using the CLI

The command-line interface provides the fastest way to interact with the launcher.

### List Scripts

```bash
python3 main.py list
```

### Get Help

```bash
python3 main.py --help
```

### Launch a Script

First, you need to register a script. You can use one of the example scripts:

```bash
# Register the hello_world script via interactive mode
python3 main.py interactive
```

Then select option 2 to launch a script.

Alternatively, you can quick-launch a script without registration:

```bash
python3 main.py quick scripts/hello_world.py
```

## Using the GUI

To start the graphical interface:

```bash
python3 main.py gui
```

The GUI provides a visual way to:

*   Browse and search registered scripts
*   Configure parameters with a form-based interface
*   Monitor execution in real-time
*   View live terminal output

## Using the API

To start the REST API server:

```bash
python3 main.py api
```

The API will be available at `http://localhost:8000`.

### API Documentation

Interactive API documentation is available at:

*   Swagger UI: `http://localhost:8000/docs`
*   ReDoc: `http://localhost:8000/redoc`

### Example API Call (using curl)

```bash
# List all scripts
curl http://localhost:8000/scripts

# Quick launch a script
curl -X POST http://localhost:8000/quick-launch \
  -H "Content-Type: application/json" \
  -d '{"script_path": "/path/to/script.py", "args": []}'
```

## Registering Your First Script

### Via CLI

Create a JSON configuration file:

```json
{
  "name": "My Script",
  "path": "/path/to/my_script.py",
  "description": "Description of my script",
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

Then import it:

```bash
python3 main.py import-config my_script_config.json
```

### Via GUI

1.  Click **Register Script** in the top menu
2.  Fill in the form
3.  Click **Register**

### Via API

```bash
curl -X POST http://localhost:8000/scripts/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Script",
    "path": "/path/to/my_script.py",
    "description": "Description of my script",
    "parameters": [],
    "tags": ["data"]
  }'
```

## Next Steps

*   Read the [User Guide](docs/USER_GUIDE.md) for detailed instructions
*   Explore the [API Guide](docs/API_GUIDE.md) for programmatic access
*   Check out the example scripts in the `scripts/` directory

