"""
Dialog for registering new scripts.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core import ScriptMetadata, ScriptParameter, get_registry


class RegisterDialog:
    """Dialog for registering a new script."""
    
    def __init__(self, parent):
        self.registry = get_registry()
        
        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Register New Script")
        self.dialog.geometry("600x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components."""
        # Main container with scrollbar
        main_frame = ctk.CTkScrollableFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Script name
        ctk.CTkLabel(main_frame, text="Script Name *", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text="My Script")
        self.name_entry.pack(fill="x", pady=(0, 15))
        
        # Script path
        ctk.CTkLabel(main_frame, text="Script Path *", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        path_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        path_frame.pack(fill="x", pady=(0, 15))
        
        self.path_entry = ctk.CTkEntry(path_frame, placeholder_text="/path/to/script.py")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(path_frame, text="Browse", width=80, command=self._browse_script).pack(side="right")
        
        # Description
        ctk.CTkLabel(main_frame, text="Description *", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.desc_text = ctk.CTkTextbox(main_frame, height=80)
        self.desc_text.pack(fill="x", pady=(0, 15))
        
        # Author
        ctk.CTkLabel(main_frame, text="Author", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.author_entry = ctk.CTkEntry(main_frame, placeholder_text="Your Name")
        self.author_entry.pack(fill="x", pady=(0, 15))
        
        # Version
        ctk.CTkLabel(main_frame, text="Version", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.version_entry = ctk.CTkEntry(main_frame, placeholder_text="1.0.0")
        self.version_entry.insert(0, "1.0.0")
        self.version_entry.pack(fill="x", pady=(0, 15))
        
        # Tags
        ctk.CTkLabel(main_frame, text="Tags (comma-separated)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.tags_entry = ctk.CTkEntry(main_frame, placeholder_text="automation, data-processing")
        self.tags_entry.pack(fill="x", pady=(0, 15))
        
        # Timeout
        ctk.CTkLabel(main_frame, text="Timeout (seconds, optional)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.timeout_entry = ctk.CTkEntry(main_frame, placeholder_text="300")
        self.timeout_entry.pack(fill="x", pady=(0, 15))
        
        # Working directory
        ctk.CTkLabel(main_frame, text="Working Directory (optional)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        wd_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        wd_frame.pack(fill="x", pady=(0, 15))
        
        self.wd_entry = ctk.CTkEntry(wd_frame, placeholder_text="/path/to/working/dir")
        self.wd_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(wd_frame, text="Browse", width=80, command=self._browse_directory).pack(side="right")
        
        # Buttons
        button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy,
            fg_color="gray"
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Register",
            command=self._register
        ).pack(side="right", padx=5)
    
    def _browse_script(self):
        """Browse for script file."""
        filename = filedialog.askopenfilename(
            title="Select Python Script",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if filename:
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, filename)
            
            # Auto-fill name if empty
            if not self.name_entry.get():
                script_name = Path(filename).stem.replace('_', ' ').title()
                self.name_entry.insert(0, script_name)
    
    def _browse_directory(self):
        """Browse for working directory."""
        dirname = filedialog.askdirectory(title="Select Working Directory")
        if dirname:
            self.wd_entry.delete(0, 'end')
            self.wd_entry.insert(0, dirname)
    
    def _register(self):
        """Register the script."""
        # Validate required fields
        name = self.name_entry.get().strip()
        path = self.path_entry.get().strip()
        description = self.desc_text.get("1.0", "end").strip()
        
        if not name:
            messagebox.showerror("Error", "Script name is required")
            return
        
        if not path:
            messagebox.showerror("Error", "Script path is required")
            return
        
        if not description:
            messagebox.showerror("Error", "Description is required")
            return
        
        # Check if file exists
        if not Path(path).exists():
            messagebox.showerror("Error", f"Script file not found: {path}")
            return
        
        # Parse tags
        tags_str = self.tags_entry.get().strip()
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        
        # Parse timeout
        timeout_str = self.timeout_entry.get().strip()
        timeout = None
        if timeout_str:
            try:
                timeout = int(timeout_str)
            except ValueError:
                messagebox.showerror("Error", "Timeout must be a number")
                return
        
        # Get optional fields
        author = self.author_entry.get().strip()
        version = self.version_entry.get().strip() or "1.0.0"
        working_dir = self.wd_entry.get().strip() or None
        
        # Create metadata
        metadata = ScriptMetadata(
            id="",
            name=name,
            path=path,
            description=description,
            author=author,
            version=version,
            tags=tags,
            timeout=timeout,
            working_directory=working_dir
        )
        
        # Register
        try:
            script_id = self.registry.register_script(metadata)
            messagebox.showinfo("Success", f"Script registered successfully!\nID: {script_id}")
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to register script: {e}")

