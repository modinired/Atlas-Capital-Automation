"""
Monitor panel for displaying execution metrics and status.
"""

import customtkinter as ctk
from typing import Optional
import time


class MonitorPanel(ctk.CTkFrame):
    """Panel for monitoring script execution."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.start_time: Optional[float] = None
        self.timer_running = False
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="📊 Execution Monitor",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        # Status frame
        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill="x", padx=10, pady=10)
        
        # Status indicator
        ctk.CTkLabel(
            status_frame,
            text="Status:",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Idle",
            text_color="gray"
        )
        self.status_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Script name
        ctk.CTkLabel(
            status_frame,
            text="Script:",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.script_label = ctk.CTkLabel(
            status_frame,
            text="-",
            wraplength=200
        )
        self.script_label.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # Metrics frame
        metrics_frame = ctk.CTkFrame(self)
        metrics_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Duration
        self._create_metric_row(metrics_frame, "⏱️ Duration:", "duration", 0)
        
        # Exit code
        self._create_metric_row(metrics_frame, "🔢 Exit Code:", "exit_code", 1)
        
        # Peak memory
        self._create_metric_row(metrics_frame, "💾 Peak Memory:", "memory", 2)
        
        # CPU usage
        self._create_metric_row(metrics_frame, "⚡ Avg CPU:", "cpu", 3)
        
        # Progress bar
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            progress_frame,
            text="Progress:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=5, pady=(5, 0))
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        self.progress_bar.set(0)
        
        # Initialize metric labels
        self.metric_labels = {}
    
    def _create_metric_row(self, parent, label_text: str, metric_name: str, row: int):
        """Create a metric row."""
        ctk.CTkLabel(
            parent,
            text=label_text,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=row, column=0, sticky="w", padx=10, pady=8)
        
        value_label = ctk.CTkLabel(
            parent,
            text="-",
            anchor="w"
        )
        value_label.grid(row=row, column=1, sticky="w", padx=10, pady=8)
        
        self.metric_labels[metric_name] = value_label
    
    def start_execution(self, script_name: str):
        """Start monitoring an execution."""
        self.start_time = time.time()
        self.timer_running = True
        
        self.status_label.configure(text="Running", text_color="green")
        self.script_label.configure(text=script_name)
        
        # Reset metrics
        for label in self.metric_labels.values():
            label.configure(text="-")
        
        self.progress_bar.set(0)
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        # Start timer update
        self._update_timer()
    
    def stop_execution(self, result):
        """Stop monitoring and display final results."""
        self.timer_running = False
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(1.0)
        
        # Update status
        if result.is_success():
            self.status_label.configure(text="Completed", text_color="green")
        else:
            self.status_label.configure(text="Failed", text_color="red")
        
        # Update metrics
        if result.metrics:
            if result.metrics.duration:
                self.metric_labels['duration'].configure(
                    text=f"{result.metrics.duration:.2f}s"
                )
            
            if result.metrics.peak_memory_mb > 0:
                self.metric_labels['memory'].configure(
                    text=f"{result.metrics.peak_memory_mb:.1f} MB"
                )
            
            if result.metrics.cpu_percent:
                avg_cpu = sum(result.metrics.cpu_percent) / len(result.metrics.cpu_percent)
                self.metric_labels['cpu'].configure(
                    text=f"{avg_cpu:.1f}%"
                )
        
        if result.exit_code is not None:
            self.metric_labels['exit_code'].configure(
                text=str(result.exit_code),
                text_color="green" if result.exit_code == 0 else "red"
            )
    
    def _update_timer(self):
        """Update the duration timer."""
        if self.timer_running and self.start_time:
            elapsed = time.time() - self.start_time
            self.metric_labels['duration'].configure(text=f"{elapsed:.1f}s")
            
            # Schedule next update
            self.after(100, self._update_timer)
    
    def reset(self):
        """Reset the monitor to idle state."""
        self.timer_running = False
        self.start_time = None
        
        self.status_label.configure(text="Idle", text_color="gray")
        self.script_label.configure(text="-")
        
        for label in self.metric_labels.values():
            label.configure(text="-", text_color="white")
        
        self.progress_bar.set(0)

