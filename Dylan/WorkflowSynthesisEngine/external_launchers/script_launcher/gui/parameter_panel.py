"""
Parameter panel for dynamic parameter configuration.
"""

import customtkinter as ctk
from typing import Callable, Dict, Any, Optional
from tkinter import filedialog
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core import ScriptMetadata, ParameterManager


class ParameterPanel(ctk.CTkFrame):
    """Panel for configuring script parameters."""
    
    def __init__(self, parent, on_launch: Callable[[str, Dict[str, Any]], None]):
        super().__init__(parent)
        
        self.on_launch = on_launch
        self.param_manager = ParameterManager()
        self.current_script: Optional[ScriptMetadata] = None
        self.param_widgets: Dict[str, Any] = {}
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components."""
        # Header
        self.header_label = ctk.CTkLabel(
            self,
            text="⚙️ Parameters",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        self.header_label.pack(fill="x", padx=10, pady=(10, 5))
        
        # Script info
        self.info_label = ctk.CTkLabel(
            self,
            text="No script selected",
            anchor="w",
            text_color="gray"
        )
        self.info_label.pack(fill="x", padx=10, pady=5)
        
        # Scrollable frame for parameters
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bottom controls
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Preset controls
        preset_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        preset_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(preset_frame, text="Preset:").pack(side="left", padx=(0, 5))
        
        self.preset_var = ctk.StringVar(value="")
        self.preset_combo = ctk.CTkComboBox(
            preset_frame,
            variable=self.preset_var,
            values=[],
            command=self._load_preset,
            width=150
        )
        self.preset_combo.pack(side="left", padx=5)
        
        ctk.CTkButton(
            preset_frame,
            text="Save",
            width=60,
            command=self._save_preset
        ).pack(side="left", padx=5)
        
        # Launch button
        self.launch_button = ctk.CTkButton(
            control_frame,
            text="🚀 Launch Script",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._launch,
            state="disabled"
        )
        self.launch_button.pack(fill="x")
    
    def load_script(self, script: ScriptMetadata):
        """Load a script and create parameter inputs."""
        self.current_script = script
        
        # Update header
        self.header_label.configure(text=f"⚙️ Parameters: {script.name}")
        self.info_label.configure(text=script.description)
        
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.param_widgets.clear()
        
        # Load presets
        presets = self.param_manager.list_presets(script.id)
        self.preset_combo.configure(values=[""] + presets)
        self.preset_var.set("")
        
        # Create parameter inputs
        if not script.parameters:
            no_params_label = ctk.CTkLabel(
                self.scrollable_frame,
                text="This script has no parameters",
                text_color="gray"
            )
            no_params_label.pack(pady=20)
        else:
            for param in script.parameters:
                self._create_parameter_widget(param)
        
        # Enable launch button
        self.launch_button.configure(state="normal")
    
    def _create_parameter_widget(self, param):
        """Create input widget for a parameter."""
        # Container frame
        frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        
        # Label
        label_text = f"{param.name}"
        if param.required:
            label_text += " *"
        
        label = ctk.CTkLabel(
            frame,
            text=label_text,
            anchor="w",
            font=ctk.CTkFont(weight="bold")
        )
        label.pack(anchor="w")
        
        # Description
        if param.description:
            desc_label = ctk.CTkLabel(
                frame,
                text=param.description,
                anchor="w",
                text_color="gray",
                font=ctk.CTkFont(size=11)
            )
            desc_label.pack(anchor="w")
        
        # Input widget based on type
        if param.type == 'bool':
            var = ctk.BooleanVar(value=param.default or False)
            widget = ctk.CTkCheckBox(frame, text="Enable", variable=var)
            widget.pack(anchor="w", pady=5)
            self.param_widgets[param.name] = var
        
        elif param.type == 'choice':
            var = ctk.StringVar(value=param.default or (param.choices[0] if param.choices else ""))
            widget = ctk.CTkComboBox(
                frame,
                variable=var,
                values=param.choices or []
            )
            widget.pack(fill="x", pady=5)
            self.param_widgets[param.name] = var
        
        elif param.type == 'file':
            var = ctk.StringVar(value=param.default or "")
            
            input_frame = ctk.CTkFrame(frame, fg_color="transparent")
            input_frame.pack(fill="x", pady=5)
            
            entry = ctk.CTkEntry(input_frame, textvariable=var)
            entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            browse_btn = ctk.CTkButton(
                input_frame,
                text="Browse",
                width=80,
                command=lambda: self._browse_file(var)
            )
            browse_btn.pack(side="right")
            
            self.param_widgets[param.name] = var
        
        elif param.type == 'directory':
            var = ctk.StringVar(value=param.default or "")
            
            input_frame = ctk.CTkFrame(frame, fg_color="transparent")
            input_frame.pack(fill="x", pady=5)
            
            entry = ctk.CTkEntry(input_frame, textvariable=var)
            entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            browse_btn = ctk.CTkButton(
                input_frame,
                text="Browse",
                width=80,
                command=lambda: self._browse_directory(var)
            )
            browse_btn.pack(side="right")
            
            self.param_widgets[param.name] = var
        
        elif param.type in ('int', 'float'):
            var = ctk.StringVar(value=str(param.default) if param.default is not None else "")
            entry = ctk.CTkEntry(frame, textvariable=var)
            entry.pack(fill="x", pady=5)
            
            # Add range hint
            if param.min_value is not None or param.max_value is not None:
                range_text = "Range: "
                if param.min_value is not None:
                    range_text += f"≥ {param.min_value}"
                if param.max_value is not None:
                    if param.min_value is not None:
                        range_text += ", "
                    range_text += f"≤ {param.max_value}"
                
                range_label = ctk.CTkLabel(
                    frame,
                    text=range_text,
                    text_color="gray",
                    font=ctk.CTkFont(size=10)
                )
                range_label.pack(anchor="w")
            
            self.param_widgets[param.name] = var
        
        else:  # string
            var = ctk.StringVar(value=param.default or "")
            entry = ctk.CTkEntry(frame, textvariable=var)
            entry.pack(fill="x", pady=5)
            self.param_widgets[param.name] = var
    
    def _browse_file(self, var: ctk.StringVar):
        """Browse for a file."""
        filename = filedialog.askopenfilename()
        if filename:
            var.set(filename)
    
    def _browse_directory(self, var: ctk.StringVar):
        """Browse for a directory."""
        dirname = filedialog.askdirectory()
        if dirname:
            var.set(dirname)
    
    def _get_parameter_values(self) -> Dict[str, Any]:
        """Get current parameter values."""
        values = {}
        for name, widget in self.param_widgets.items():
            if isinstance(widget, ctk.BooleanVar):
                values[name] = widget.get()
            elif isinstance(widget, ctk.StringVar):
                value = widget.get()
                values[name] = value if value else None
            else:
                values[name] = widget.get()
        return values
    
    def _launch(self):
        """Launch the script with current parameters."""
        if not self.current_script:
            return
        
        values = self._get_parameter_values()
        self.on_launch(self.current_script.id, values)
    
    def _save_preset(self):
        """Save current parameters as a preset."""
        if not self.current_script:
            return
        
        from tkinter import simpledialog
        preset_name = simpledialog.askstring(
            "Save Preset",
            "Enter preset name:",
            parent=self
        )
        
        if preset_name:
            values = self._get_parameter_values()
            success = self.param_manager.save_parameter_preset(
                preset_name,
                self.current_script.id,
                values
            )
            
            if success:
                # Refresh preset list
                presets = self.param_manager.list_presets(self.current_script.id)
                self.preset_combo.configure(values=[""] + presets)
                self.preset_var.set(preset_name)
    
    def _load_preset(self, preset_name: str):
        """Load a parameter preset."""
        if not self.current_script or not preset_name:
            return
        
        values = self.param_manager.load_parameter_preset(preset_name, self.current_script.id)
        if values:
            # Set parameter values
            for name, value in values.items():
                if name in self.param_widgets:
                    widget = self.param_widgets[name]
                    if isinstance(widget, ctk.BooleanVar):
                        widget.set(bool(value))
                    elif isinstance(widget, ctk.StringVar):
                        widget.set(str(value) if value is not None else "")

