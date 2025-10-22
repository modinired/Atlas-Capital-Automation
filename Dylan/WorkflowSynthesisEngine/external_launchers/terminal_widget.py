"""
Terminal widget for displaying live script output with ANSI color support.
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import re


class TerminalWidget(ctk.CTkFrame):
    """Terminal widget for displaying script output."""
    
    # ANSI color codes mapping
    ANSI_COLORS = {
        '30': 'black', '31': 'red', '32': 'green', '33': 'yellow',
        '34': 'blue', '35': 'magenta', '36': 'cyan', '37': 'white',
        '90': 'gray', '91': 'lightred', '92': 'lightgreen', '93': 'lightyellow',
        '94': 'lightblue', '95': 'lightmagenta', '96': 'lightcyan', '97': 'lightgray'
    }
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self._create_ui()
        self._configure_tags()
    
    def _create_ui(self):
        """Create UI components."""
        # Header with controls
        header = ctk.CTkFrame(self, height=35, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        
        title_label = ctk.CTkLabel(
            header,
            text="💻 Terminal Output",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(side="left", padx=10)
        
        # Control buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        self.autoscroll_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            btn_frame,
            text="Auto-scroll",
            variable=self.autoscroll_var,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Clear",
            width=60,
            command=self.clear
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Copy",
            width=60,
            command=self.copy_to_clipboard
        ).pack(side="left", padx=5)
        
        # Text widget with scrollbar
        text_frame = ctk.CTkFrame(self)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Use tk.Text for better control over text formatting
        self.text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Monaco", 11) if tk.TkVersion >= 8.6 else ("Courier", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            selectbackground="#264f78",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        
        scrollbar = ctk.CTkScrollbar(text_frame, command=self.text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        self.text_widget.pack(side="left", fill="both", expand=True)
    
    def _configure_tags(self):
        """Configure text tags for different output types."""
        # Standard output types
        self.text_widget.tag_config('stdout', foreground='#d4d4d4')
        self.text_widget.tag_config('stderr', foreground='#f48771')
        self.text_widget.tag_config('info', foreground='#4ec9b0')
        self.text_widget.tag_config('success', foreground='#89d185')
        self.text_widget.tag_config('error', foreground='#f48771')
        self.text_widget.tag_config('warning', foreground='#dcdcaa')
        self.text_widget.tag_config('timestamp', foreground='#808080')
        
        # ANSI colors
        for code, color_name in self.ANSI_COLORS.items():
            self.text_widget.tag_config(f'ansi_{code}', foreground=color_name)
    
    def _strip_ansi_codes(self, text: str) -> str:
        """Remove ANSI escape codes from text."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def _parse_ansi_text(self, text: str) -> list:
        """Parse text with ANSI codes into segments."""
        # Simple ANSI parser for basic color support
        ansi_pattern = re.compile(r'\x1B\[([0-9;]+)m')
        segments = []
        current_pos = 0
        current_tags = []
        
        for match in ansi_pattern.finditer(text):
            # Add text before this code
            if match.start() > current_pos:
                segments.append((text[current_pos:match.start()], current_tags.copy()))
            
            # Parse ANSI code
            codes = match.group(1).split(';')
            for code in codes:
                if code == '0':  # Reset
                    current_tags = []
                elif code in self.ANSI_COLORS:
                    current_tags.append(f'ansi_{code}')
            
            current_pos = match.end()
        
        # Add remaining text
        if current_pos < len(text):
            segments.append((text[current_pos:], current_tags.copy()))
        
        return segments if segments else [(text, [])]
    
    def write(self, text: str, tag: str = 'stdout', add_timestamp: bool = False):
        """Write text to terminal with optional tag."""
        self.text_widget.configure(state='normal')
        
        if add_timestamp:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.text_widget.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # Check for ANSI codes
        if '\x1B[' in text:
            segments = self._parse_ansi_text(text)
            for segment_text, ansi_tags in segments:
                tags = [tag] + ansi_tags
                self.text_widget.insert(tk.END, segment_text, tuple(tags))
        else:
            self.text_widget.insert(tk.END, text, tag)
        
        self.text_widget.insert(tk.END, '\n')
        
        # Auto-scroll
        if self.autoscroll_var.get():
            self.text_widget.see(tk.END)
        
        self.text_widget.configure(state='disabled')
    
    def write_stdout(self, text: str):
        """Write stdout text."""
        self.write(text, 'stdout', add_timestamp=False)
    
    def write_stderr(self, text: str):
        """Write stderr text."""
        self.write(text, 'stderr', add_timestamp=False)
    
    def write_info(self, text: str):
        """Write info message."""
        self.write(text, 'info', add_timestamp=True)
    
    def write_success(self, text: str):
        """Write success message."""
        self.write(text, 'success', add_timestamp=True)
    
    def write_error(self, text: str):
        """Write error message."""
        self.write(text, 'error', add_timestamp=True)
    
    def write_warning(self, text: str):
        """Write warning message."""
        self.write(text, 'warning', add_timestamp=True)
    
    def clear(self):
        """Clear terminal output."""
        self.text_widget.configure(state='normal')
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.configure(state='disabled')
    
    def copy_to_clipboard(self):
        """Copy terminal content to clipboard."""
        content = self.text_widget.get('1.0', tk.END)
        self.clipboard_clear()
        self.clipboard_append(content)
    
    def get_content(self) -> str:
        """Get all terminal content."""
        return self.text_widget.get('1.0', tk.END)

