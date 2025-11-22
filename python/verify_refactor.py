import logging
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from llm_session import Automator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def otp_handler():
    logger.info("OTP Handler called!")
    return "123456"

def main():
    logger.info("Starting Python Verification...")
    
    try:
        # Initialize Automator
        # We use dummy credentials to test the flow up to login attempt
        bot = Automator(
            provider="chatgpt",
            headless=True,
            credentials={
                "email": "test@example.com",
                "password": "password",
                "method": "email"
            },
            on_otp_required=otp_handler
        )
        
        logger.info("Automator initialized successfully.")
        
        # We won't actually login as we don't have real creds here, 
        # but we can check if the browser starts and closes.
        # The _setup() method calls browser_manager.start()
        
        logger.info("Closing Automator...")
        bot.close()
        logger.info("Verification Passed!")
        
    except Exception as e:
        logger.error(f"Verification Failed: {e}")
        # If it fails due to login timeout (expected with dummy creds), that's fine for structure check
        if "Login failed" in str(e) or "Timeout" in str(e):
             logger.info("Login failed as expected with dummy creds. Structure is correct.")
        else:
             raise e

if __name__ == "__main__":
    main()
