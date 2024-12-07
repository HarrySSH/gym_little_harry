# main.py
from gym_little_harry import setup_logging, ChatbotApp
def main():
    # Your Hugging Face token
    token = "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"
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Phi Chatbot application")
    
    try:
        app = ChatbotApp(token)
        app.run()
    except Exception as e:
        logger.error(f"Critical application error: {str(e)}")

if __name__ == "__main__":
    main()