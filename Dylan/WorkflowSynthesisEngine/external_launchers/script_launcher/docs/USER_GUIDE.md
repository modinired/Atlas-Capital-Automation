# User Guide

Welcome to the Script Launcher Pro! This guide will walk you through using the GUI and CLI interfaces to manage and execute your Python scripts.

## GUI Interface

The GUI provides a user-friendly, visual way to interact with the script launcher.

### Main Window

The main window is divided into four main sections:

1.  **Scripts Panel (Left)**: Lists all registered scripts. You can search for scripts and filter by status (all/enabled).
2.  **Parameters Panel (Top-Right)**: Configure the parameters for the selected script before launching.
3.  **Execution Monitor (Top-Right)**: Displays real-time metrics for the currently running script, such as status, duration, and resource usage.
4.  **Terminal Panel (Bottom-Right)**: Shows the live output (stdout and stderr) of the executed script.

### Registering a Script

1.  Click the **Register Script** button in the top menu.
2.  Fill in the required details in the dialog:
    *   **Script Name**: A user-friendly name for your script.
    *   **Script Path**: The absolute path to the Python script file.
    *   **Description**: A brief description of what the script does.
3.  Click **Register**.

### Launching a Script

1.  Select a script from the **Scripts Panel**.
2.  The **Parameters Panel** will load the script's parameters.
3.  Fill in the required parameter values.
4.  Click the **Launch Script** button.
5.  The script will execute, and you can monitor its progress and see its output in the respective panels.

### Using Presets

You can save and load parameter configurations as presets:

*   **Save**: After configuring parameters, click the **Save** button next to the preset dropdown, and enter a name for the preset.
*   **Load**: Select a saved preset from the dropdown menu to automatically fill in the parameter values.

## CLI Interface

The CLI is ideal for automation, scripting, and for users who prefer the command line.

### Basic Commands

*   **`list`**: List all registered scripts.

    ```bash
    python3 main.py list
    ```

*   **`info <script_id>`**: Show detailed information about a specific script.

    ```bash
    python3 main.py info <script_id>
    ```

*   **`launch <script_id>`**: Launch a script.

    ```bash
    python3 main.py launch <script_id> --param name=value
    ```

*   **`history`**: Show the execution history.

    ```bash
    python3 main.py history
    ```

### Launching with Parameters

You can provide parameters using the `--param` or `-p` option:

```bash
python3 main.py launch <script_id> -p name="John Doe" -p age=30
```

### Interactive Mode

For a guided CLI experience, use the interactive mode:

```bash
python3 main.py interactive
```

This mode provides a menu-driven interface for all the main functions of the launcher.

