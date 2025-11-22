import os
from typing import Optional

class Config:
    """Configuration handler for LLM Automator."""
    
    @staticmethod
    def get_credentials(provider: str) -> dict:
        """
        Retrieve credentials for a specific provider from environment variables.
        
        Args:
            provider: The name of the provider (e.g., 'chatgpt').
            
        Returns:
            dict: A dictionary containing credentials.
        """
        if provider.lower() == "chatgpt":
            return {
                "email": os.environ.get("CHATGPT_EMAIL"),
                "password": os.environ.get("CHATGPT_PASSWORD"),
                "google_login": os.environ.get("CHATGPT_GOOGLE_LOGIN", "false").lower() == "true"
            }
        return {}

    @staticmethod
    def get_headless_mode() -> bool:
        """Check if headless mode is enabled (default: False for debug, True for prod usually, but MVP says non-interactive)."""
        # For the MVP, we want it to be non-interactive, so headless=True by default unless specified.
        return os.environ.get("LLM_AUTOMATOR_HEADLESS", "true").lower() == "true"
