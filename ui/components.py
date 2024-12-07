import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)

class LoadingIndicator(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        
        # Loading label
        self.loading_label = ctk.CTkLabel(self, text="Generating response...", font=("Arial", 12))
        self.loading_label.pack(pady=5)
        
        # Create dots animation frames
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_frame = 0
        
        # Spinner label
        self.spinner_label = ctk.CTkLabel(self, text=self.frames[0], font=("Arial", 14))
        self.spinner_label.pack(pady=5)
        
        self.is_animating = False
        
    def start(self):
        logger.debug("Starting loading animation")
        self.is_animating = True
        self.animate()
        self.pack(pady=10)
        
    def stop(self):
        logger.debug("Stopping loading animation")
        self.is_animating = False
        self.pack_forget()
        
    def animate(self):
        if self.is_animating:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.spinner_label.configure(text=self.frames[self.current_frame])
            self.after(100, self.animate)