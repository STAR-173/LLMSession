from abc import ABC, abstractmethod
from playwright.sync_api import Page

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, page: Page):
        self.page = page

    @abstractmethod
    def login(self, credentials: dict) -> bool:
        """
        Perform login sequence.
        
        Args:
            credentials: Dictionary of credentials.
            
        Returns:
            bool: True if login successful.
        """
        pass

    @abstractmethod
    def send_prompt(self, prompt: str) -> str:
        """
        Send a prompt and get the response.
        
        Args:
            prompt: The text prompt.
            
        Returns:
            str: The model's response.
        """
        pass
    
    @abstractmethod
    def handle_dialogs(self):
        """Check for and dismiss known dialogs."""
        pass
