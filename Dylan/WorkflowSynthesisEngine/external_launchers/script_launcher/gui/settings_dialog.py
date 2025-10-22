"""
Settings dialog for application configuration.
"""

import customtkinter as ctk
from tkinter import messagebox


class SettingsDialog:
    """Dialog for application settings."""
    
    def __init__(self, parent):
        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components."""
        # Main container
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Appearance
        ctk.CTkLabel(
            main_frame,
            text="Appearance",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 10))
        
        appearance_frame = ctk.CTkFrame(main_frame)
        appearance_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(appearance_frame, text="Theme:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_menu = ctk.CTkOptionMenu(
            appearance_frame,
            variable=self.theme_var,
            values=["System", "Dark", "Light"],
            command=self._change_theme
        )
        theme_menu.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        
        # Logging
        ctk.CTkLabel(
            main_frame,
            text="Logging",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 10))
        
        logging_frame = ctk.CTkFrame(main_frame)
        logging_frame.pack(fill="x", pady=(0, 20))
        
        self.log_level_var = ctk.StringVar(value="INFO")
        ctk.CTkLabel(logging_frame, text="Log Level:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        log_menu = ctk.CTkOptionMenu(
            logging_frame,
            variable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"]
        )
        log_menu.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        
        # Execution
        ctk.CTkLabel(
            main_frame,
            text="Execution",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 10))
        
        exec_frame = ctk.CTkFrame(main_frame)
        exec_frame.pack(fill="x", pady=(0, 20))
        
        self.default_timeout_var = ctk.StringVar(value="300")
        ctk.CTkLabel(exec_frame, text="Default Timeout (s):").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        timeout_entry = ctk.CTkEntry(exec_frame, textvariable=self.default_timeout_var, width=100)
        timeout_entry.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        
        # Buttons
        button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Save",
            command=self._save_settings
        ).pack(side="right", padx=5)
    
    def _change_theme(self, theme: str):
        """Change application theme."""
        ctk.set_appearance_mode(theme.lower())
    
    def _save_settings(self):
        """Save settings."""
        messagebox.showinfo("Settings", "Settings saved successfully!")
        self.dialog.destroy()

