'''# Script Launcher Pro

**PhD-quality, world-class, production-ready Python script launcher interface.**

This application provides a comprehensive solution for managing and executing Python scripts through multiple interfaces: a modern graphical user interface (GUI), a powerful command-line interface (CLI), and a REST API for programmatic access by coding agents.

![GUI Screenshot](docs/screenshot.png) <!-- placeholder for a screenshot -->

## 🌟 Features

- **Multi-Interface Access**: Manage and launch scripts through a macOS-optimized GUI, a feature-rich CLI, or a REST API.
- **Comprehensive Script Management**: Register, configure, and organize scripts with detailed metadata, including parameters, tags, and versioning.
- **Dynamic Parameter Configuration**: Define and validate script parameters with support for various data types (string, int, float, bool, file, choice).
- **Real-time Execution Monitoring**: Monitor script execution in real-time with live output streaming, status updates, and resource usage metrics (CPU, memory).
- **Scheduling and Automation**: Schedule scripts to run at specific times, at regular intervals, or using cron expressions.
- **Production-Grade Logging**: Centralized logging system with log rotation, color-coded output, and dedicated log files for each script execution.
- **Agent-Friendly API**: A robust REST API with JSON-based communication, allowing for seamless integration with AI agents and automation tools.
- **Interactive CLI Mode**: An interactive terminal UI for a guided and user-friendly command-line experience.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+

### Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd script_launcher
    ```

2.  **Install dependencies:**

    ```bash
    pip3 install -r requirements.txt
    ```

### Running the Application

You can launch the application in three different modes:

1.  **GUI Mode**:

    ```bash
    python3 main.py gui
    ```

2.  **CLI Mode**:

    ```bash
    python3 main.py --help
    ```

3.  **API Server**:

    ```bash
    python3 main.py api
    ```

    The API will be available at `http://localhost:8000`, with documentation at `http://localhost:8000/docs`.

## 📖 Documentation

- **[User Guide](docs/USER_GUIDE.md)**: A comprehensive guide to using the GUI and CLI interfaces.
- **[API Guide](docs/API_GUIDE.md)**: Detailed documentation for the REST API.
- **[Architecture](docs/ARCHITECTURE.md)**: An overview of the project's architecture and design patterns.

## 🧪 Example Scripts

The `scripts/` directory contains example scripts that demonstrate the launcher's features. You can register these scripts in the application to see how they work.

- **`hello_world.py`**: A simple script that prints a greeting.
- **`parameter_test.py`**: A script that demonstrates various parameter types.
- **`long_running_task.py`**: A script that simulates a long-running process with logging.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
'''
