import customtkinter as ctk
import logging
from queue import Queue
from threading import Thread
from .components import LoadingIndicator
from ..core.model import ModelManager
from ..config.settings import WINDOW_TITLE, WINDOW_SIZE

logger = logging.getLogger(__name__)

class ChatbotApp:
    def __init__(self, token):
        logger.info("Initializing ChatbotApp")
        self.window = ctk.CTk()
        self.window.title(WINDOW_TITLE)
        self.window.geometry(WINDOW_SIZE)
        
        # Initialize model manager
        self.model_manager = ModelManager(token)
        
        # Initialize message queue
        self.message_queue = Queue()
        self.is_processing = False
        
        # Setup UI
        logger.debug("Setting up UI components")
        self.setup_ui()
        
        # Initialize model
        if not self.model_manager.initialize():
            self.add_message("System", "Failed to initialize model")
            return
        
        # Start processing thread
        logger.debug("Starting message processing thread")
        self.process_thread = Thread(target=self.process_messages, daemon=True)
        self.process_thread.start()

    def setup_ui(self):
        # Create chat display
        self.chat_frame = ctk.CTkFrame(self.window)
        self.chat_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.chat_display = ctk.CTkTextbox(self.chat_frame)
        self.chat_display.pack(fill="both", expand=True, padx=5, pady=5)
        self.chat_display.configure(state="normal")
        
        # Create loading indicator
        self.loading_indicator = LoadingIndicator(self.chat_frame)
        
        # Create input area
        self.input_frame = ctk.CTkFrame(self.window)
        self.input_frame.pack(fill="x", padx=10, pady=5)
        
        self.input_box = ctk.CTkTextbox(self.input_frame, height=50)
        self.input_box.pack(side="left", fill="x", expand=True, padx=(5, 2), pady=5)
        
        self.send_button = ctk.CTkButton(
            self.input_frame, 
            text="Send", 
            command=self.send_message
        )
        self.send_button.pack(side="right", padx=(2, 5), pady=5)
        
        # Bind Enter key to send message
        self.input_box.bind("<Return>", lambda event: self.send_message())
        logger.debug("UI setup completed")

    def send_message(self):
        try:
            message = self.input_box.get("1.0", "end-1c").strip()
            if message:
                logger.info(f"Sending message: {message}")
                self.input_box.delete("1.0", "end")
                self.add_message("You", message)
                self.message_queue.put(message)
                self.loading_indicator.start()
                self.send_button.configure(state="disabled")
        except Exception as e:
            error_msg = f"Error sending message: {str(e)}"
            logger.error(error_msg)
            self.add_message("System", error_msg)

    def add_message(self, sender, message):
        try:
            logger.debug(f"Adding message from {sender}")
            self.chat_display.configure(state="normal")
            self.chat_display.insert("end", f"{sender}: {message}\n\n")
            self.chat_display.configure(state="disabled")
            self.chat_display.see("end")
            self.window.update()
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")

    def process_messages(self):
        while True:
            try:
                message = self.message_queue.get()
                logger.debug("Processing message from queue")
                self.is_processing = True
                
                response = self.model_manager.generate_response(message)
                
                def complete_response():
                    self.add_message("Assistant", response)
                    self.loading_indicator.stop()
                    self.send_button.configure(state="normal")
                    self.is_processing = False
                    logger.debug("Message processing completed")
                
                self.window.after(0, complete_response)
                
            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                logger.error(error_msg)
                self.window.after(0, self.add_message, "System", error_msg)
                self.window.after(0, self.loading_indicator.stop)
                self.window.after(0, lambda: self.send_button.configure(state="normal"))

    def run(self):
        try:
            logger.info("Starting application main loop")
            self.window.mainloop()
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
