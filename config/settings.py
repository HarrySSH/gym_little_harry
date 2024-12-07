import os

# Model settings
MODEL_NAME = "microsoft/Phi-3-mini-128k-instruct"
DEVICE = "cpu"
MAX_NEW_TOKENS = 500
TEMPERATURE = 0.7

# UI settings
WINDOW_TITLE = "Phi-3 Chatbot"
WINDOW_SIZE = "800x600"

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)