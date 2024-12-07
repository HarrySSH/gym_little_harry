import logging
import time
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from huggingface_hub import login
from ..config.settings import MODEL_NAME, DEVICE, MAX_NEW_TOKENS, TEMPERATURE

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self, token):
        self.token = token
        self.tokenizer = None
        self.model = None
        self.pipe = None

    def initialize(self):
        """Initialize the model and tokenizer."""
        try:
            logger.info("Logging in to Hugging Face...")
            login(token=self.token)
            logger.info("Successfully logged in to Hugging Face")
            
            self._load_model()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            return False

    def _load_model(self):
        """Load the model and tokenizer."""
        try:
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            logger.info("Tokenizer loaded successfully")
            
            logger.info("Loading model (this may take a while)...")
            start_time = time.time()
            self.model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                device_map=DEVICE,
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
        """Generate a response using the model."""
        try:
            logger.info("Generating response...")
            start_time = time.time()
            
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": message}
            ]
            
            generation_args = {
                "max_new_tokens": MAX_NEW_TOKENS,
                "return_full_text": False,
                "temperature": TEMPERATURE,
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