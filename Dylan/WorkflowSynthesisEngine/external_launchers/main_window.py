"""
Main GUI window using CustomTkinter for modern macOS-optimized interface.
"""

import customtkinter as ctk
from typing import Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core import get_engine, get_registry, get_logger
from .script_panel import ScriptPanel
from .parameter_panel import ParameterPanel
from .terminal_widget import TerminalWidget
from .monitor_panel import MonitorPanel

logger = get_logger(__name__)


class ScriptLauncherGUI:
    """Main GUI application for the script launcher."""
    
    def __init__(self):
        # Set appearance mode and color theme
        ctk.set_appearance_mode("system")  # Modes: "system", "dark", "light"
        ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Script Launcher Pro")
        self.root.geometry("1400x900")
        
        # Set minimum window size
        self.root.minsize(1200, 700)
        
        # Get core components
        self.engine = get_engine()
        self.registry = get_registry()
        
        # Current state
        self.selected_script_id: Optional[str] = None
        
        # Create UI
        self._create_menu_bar()
        self._create_layout()
        
        logger.info("GUI initialized")
    
    def _create_menu_bar(self):
        """Create menu bar (simplified for cross-platform compatibility)."""
        # Menu frame at top
        self.menu_frame = ctk.CTkFrame(self.root, height=40, corner_radius=0)
        self.menu_frame.pack(fill="x", side="top")
        
        # Title label
        title_label = ctk.CTkLabel(
            self.menu_frame,
            text="🚀 Script Launcher Pro",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=5)
        
        # Menu buttons
        btn_frame = ctk.CTkFrame(self.menu_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Register Script",
            width=120,
            command=self._register_new_script
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Import Config",
            width=120,
            command=self._import_config
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Settings",
            width=100,
            command=self._show_settings
        ).pack(side="left", padx=5)
    
    def _create_layout(self):
        """Create main layout with panels."""
        # Main container
        main_container = ctk.CTkFrame(self.root, corner_radius=0)
        main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Left panel - Script list
        left_panel = ctk.CTkFrame(main_container, width=300)
        left_panel.pack(side="left", fill="both", padx=10, pady=10)
        left_panel.pack_propagate(False)
        
        # Script panel
        self.script_panel = ScriptPanel(left_panel, self._on_script_selected)
        self.script_panel.pack(fill="both", expand=True)
        
        # Right side - split into top and bottom
        right_container = ctk.CTkFrame(main_container, corner_radius=0, fg_color="transparent")
        right_container.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)
        
        # Top section - Parameters and Monitor
        top_section = ctk.CTkFrame(right_container)
        top_section.pack(fill="both", expand=True, pady=(0, 10))
        
        # Parameter panel (left side of top section)
        param_frame = ctk.CTkFrame(top_section)
        param_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.parameter_panel = ParameterPanel(param_frame, self._on_launch_clicked)
        self.parameter_panel.pack(fill="both", expand=True)
        
        # Monitor panel (right side of top section)
        monitor_frame = ctk.CTkFrame(top_section, width=350)
        monitor_frame.pack(side="right", fill="both", padx=(5, 0))
        monitor_frame.pack_propagate(False)
        
        self.monitor_panel = MonitorPanel(monitor_frame)
        self.monitor_panel.pack(fill="both", expand=True)
        
        # Bottom section - Terminal
        terminal_frame = ctk.CTkFrame(right_container, height=300)
        terminal_frame.pack(fill="both", expand=False)
        terminal_frame.pack_propagate(False)
        
        self.terminal_widget = TerminalWidget(terminal_frame)
        self.terminal_widget.pack(fill="both", expand=True)
        
        # Status bar
        self.status_bar = ctk.CTkLabel(
            self.root,
            text="Ready",
            anchor="w",
            height=25
        )
        self.status_bar.pack(fill="x", side="bottom", padx=10, pady=5)
    
    def _on_script_selected(self, script_id: str):
        """Handle script selection."""
        self.selected_script_id = script_id
        script = self.registry.get_script(script_id)
        
        if script:
            self.parameter_panel.load_script(script)
            self.status_bar.configure(text=f"Selected: {script.name}")
            logger.info(f"Script selected: {script.name}")
    
    def _on_launch_clicked(self, script_id: str, parameters: dict):
        """Handle launch button click."""
        script = self.registry.get_script(script_id)
        if not script:
            self.terminal_widget.write_error("Script not found")
            return
        
        self.status_bar.configure(text=f"Launching: {script.name}...")
        self.terminal_widget.clear()
        self.terminal_widget.write_info(f"=== Launching {script.name} ===")
        self.terminal_widget.write_info(f"Parameters: {parameters}")
        
        # Update monitor
        self.monitor_panel.start_execution(script.name)
        
        # Launch in background thread
        import threading
        
        def launch_thread():
            def output_callback(stream_name: str, line: str):
                if stream_name == 'stdout':
                    self.terminal_widget.write_stdout(line)
                else:
                    self.terminal_widget.write_stderr(line)
            
            result = self.engine.launch_script(
                script_id=script_id,
                parameters=parameters,
                output_callback=output_callback,
                async_mode=False
            )
            
            # Update UI on completion
            self.root.after(0, lambda: self._on_execution_complete(script, result))
        
        thread = threading.Thread(target=launch_thread, daemon=True)
        thread.start()
    
    def _on_execution_complete(self, script, result):
        """Handle execution completion."""
        self.monitor_panel.stop_execution(result)
        
        if result.is_success():
            self.terminal_widget.write_success(f"\n=== Execution completed successfully ===")
            self.status_bar.configure(text=f"Completed: {script.name}")
        else:
            self.terminal_widget.write_error(f"\n=== Execution failed ===")
            self.status_bar.configure(text=f"Failed: {script.name}")
        
        if result.metrics:
            self.terminal_widget.write_info(f"Duration: {result.metrics.duration:.2f}s")
            self.terminal_widget.write_info(f"Peak Memory: {result.metrics.peak_memory_mb:.1f} MB")
    
    def _register_new_script(self):
        """Open dialog to register a new script."""
        from .register_dialog import RegisterDialog
        dialog = RegisterDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        # Refresh script list
        self.script_panel.refresh()
    
    def _import_config(self):
        """Import script configuration from file."""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Import Script Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            script_id = self.registry.import_script_config(filename)
            if script_id:
                self.terminal_widget.write_success(f"Script imported successfully: {script_id}")
                self.script_panel.refresh()
            else:
                self.terminal_widget.write_error("Failed to import script configuration")
    
    def _show_settings(self):
        """Show settings dialog."""
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.root)
        self.root.wait_window(dialog.dialog)
    
    def run(self):
        """Start the GUI application."""
        logger.info("Starting GUI application")
        self.root.mainloop()


def main():
    """Main entry point for GUI."""
    app = ScriptLauncherGUI()
    app.run()


if __name__ == "__main__":
    main()

