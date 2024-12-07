import customtkinter as ctk
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from threading import Thread
from queue import Queue
from huggingface_hub import login
import logging
from datetime import datetime
import time
from typing import Optional

# Enhanced logging setup
def setup_logging():
    # Create logs directory if it doesn't exist
    import os
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Setup file handler with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_handler = logging.FileHandler(f'logs/chatbot_{timestamp}.log')
    file_handler.setLevel(logging.DEBUG)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatters and add it to the handlers
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # Get the root logger and add handlers
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

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

class ChatbotApp:
    def __init__(self):
        logger.info("Initializing ChatbotApp")
        self.window = ctk.CTk()
        self.window.title("Phi-3 Chatbot")
        self.window.geometry("800x600")
        
        # Initialize message queue
        self.message_queue = Queue()
        self.is_processing = False
        
        # Setup UI first so we can show loading status
        logger.debug("Setting up UI components")
        self.setup_ui()
        
        # Login to Hugging Face

        # Load model
        self.load_model()
        
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

    def load_model(self):
        try:
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-128k-instruct")
            logger.info("Tokenizer loaded successfully")
            
            logger.info("Loading model (this may take a while)...")
            start_time = time.time()
            self.model = AutoModelForCausalLM.from_pretrained( 
                "microsoft/Phi-3-mini-128k-instruct",  
                device_map="cpu",  
                torch_dtype="auto",  
                trust_remote_code=True,  
            )
            load_time = time.time() - start_time
            logger.info(f"Model loaded successfully in {load_time:.2f} seconds")
            
            logger.info("Setting up pipeline...")
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
            )
            logger.info("Pipeline setup complete")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def generate_response(self, message: str) -> str:
        try:
            logger.info("Generating response...")
            start_time = time.time()
            
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": message}
            ]
            
            generation_args = {
                "max_new_tokens": 500,
                "return_full_text": False,
                "temperature": 0.7,
                "do_sample": True
            }
            
            logger.debug(f"Generation arguments: {generation_args}")
            output = self.pipe(messages, **generation_args)
            response = output[0]['generated_text']
            
            generation_time = time.time() - start_time
            logger.info(f"Response generated in {generation_time:.2f} seconds")
            
            return response.strip()
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def process_messages(self):
        while True:
            try:
                message = self.message_queue.get()
                logger.debug("Processing message from queue")
                self.is_processing = True
                
                response = self.generate_response(message)
                
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

if __name__ == "__main__":
    try:
        # Setup logging first
        logger = setup_logging()
        logger.info("Starting Chatbot application")
        
        app = ChatbotApp()
        app.run()
    except Exception as e:
        logger.error(f"Critical application error: {str(e)}")