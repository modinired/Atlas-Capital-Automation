"""
Script panel for displaying and selecting registered scripts.
"""

import customtkinter as ctk
from typing import Callable, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core import get_registry


class ScriptPanel(ctk.CTkFrame):
    """Panel for displaying and managing scripts."""
    
    def __init__(self, parent, on_select: Callable[[str], None]):
        super().__init__(parent)
        
        self.registry = get_registry()
        self.on_select = on_select
        self.selected_script_id: Optional[str] = None
        self.script_buttons = {}
        
        self._create_ui()
        self.refresh()
    
    def _create_ui(self):
        """Create UI components."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="📋 Scripts",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        # Search box
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda *args: self.refresh())
        
        search_entry = ctk.CTkEntry(
            self,
            placeholder_text="🔍 Search scripts...",
            textvariable=self.search_var
        )
        search_entry.pack(fill="x", padx=10, pady=5)
        
        # Filter buttons
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        self.filter_var = ctk.StringVar(value="all")
        
        ctk.CTkRadioButton(
            filter_frame,
            text="All",
            variable=self.filter_var,
            value="all",
            command=self.refresh
        ).pack(side="left", padx=5)
        
        ctk.CTkRadioButton(
            filter_frame,
            text="Enabled",
            variable=self.filter_var,
            value="enabled",
            command=self.refresh
        ).pack(side="left", padx=5)
        
        # Scrollable frame for scripts
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Count label
        self.count_label = ctk.CTkLabel(
            self,
            text="0 scripts",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.count_label.pack(pady=(0, 10))
    
    def refresh(self):
        """Refresh the script list."""
        # Clear existing buttons
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.script_buttons.clear()
        
        # Get scripts based on filter
        search_query = self.search_var.get().strip()
        filter_mode = self.filter_var.get()
        
        if search_query:
            scripts = self.registry.search_scripts(search_query)
        elif filter_mode == "enabled":
            scripts = self.registry.get_enabled_scripts()
        else:
            scripts = self.registry.get_all_scripts()
        
        # Sort by name
        scripts = sorted(scripts, key=lambda s: s.name.lower())
        
        # Create buttons for each script
        for script in scripts:
            self._create_script_button(script)
        
        # Update count
        self.count_label.configure(text=f"{len(scripts)} script{'s' if len(scripts) != 1 else ''}")
    
    def _create_script_button(self, script):
        """Create a button for a script."""
        # Container frame
        frame = ctk.CTkFrame(self.scrollable_frame)
        frame.pack(fill="x", pady=5)
        
        # Main button
        btn_text = f"{'✓' if script.enabled else '✗'} {script.name}"
        if script.tags:
            btn_text += f"\n🏷️ {', '.join(script.tags[:3])}"
        
        button = ctk.CTkButton(
            frame,
            text=btn_text,
            anchor="w",
            height=60,
            command=lambda: self._select_script(script.id),
            fg_color=("gray75", "gray25") if not script.enabled else None
        )
        button.pack(fill="x", side="left", expand=True, padx=(0, 5))
        
        # Info button
        info_btn = ctk.CTkButton(
            frame,
            text="ℹ️",
            width=40,
            command=lambda: self._show_script_info(script)
        )
        info_btn.pack(side="right")
        
        self.script_buttons[script.id] = button
    
    def _select_script(self, script_id: str):
        """Select a script."""
        self.selected_script_id = script_id
        
        # Update button colors
        for sid, button in self.script_buttons.items():
            if sid == script_id:
                button.configure(fg_color=("green", "darkgreen"))
            else:
                script = self.registry.get_script(sid)
                if script and not script.enabled:
                    button.configure(fg_color=("gray75", "gray25"))
                else:
                    button.configure(fg_color=("gray70", "gray30"))
        
        # Notify parent
        self.on_select(script_id)
    
    def _show_script_info(self, script):
        """Show detailed script information."""
        from tkinter import messagebox
        
        info = f"Name: {script.name}\n"
        info += f"Version: {script.version}\n"
        info += f"Author: {script.author}\n\n"
        info += f"Description:\n{script.description}\n\n"
        info += f"Path: {script.path}\n"
        info += f"Parameters: {len(script.parameters)}\n"
        info += f"Runs: {script.run_count} (✓{script.success_count} ✗{script.failure_count})\n"
        
        if script.last_run:
            info += f"Last run: {script.last_run}\n"
        
        messagebox.showinfo(f"Script Info: {script.name}", info)

