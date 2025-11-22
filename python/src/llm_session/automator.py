from typing import List, Optional, Callable, Union
import logging
from .browser import BrowserManager
from .config import Config
from .providers.chatgpt import ChatGPTProvider
from .exceptions import SetupError, OTPRequiredError

logger = logging.getLogger(__name__)

class Automator:
    """
    Main entry point for the LLM Web Automator.
    """

    def __init__(self, provider: str = "chatgpt", headless: bool = True, credentials: Optional[dict] = None, session_path: Optional[str] = None, config: Optional[dict] = None, on_otp_required: Optional[Callable[[], str]] = None):
        self.provider_name = provider
        self.headless = headless
        self.credentials = credentials
        self.session_path = session_path
        self.config = config or {}
        self.on_otp_required = on_otp_required
        self.browser_manager = BrowserManager()
        self.provider = None
        
        # Initialize
        self._setup()

    def _setup(self):
        """Initialize browser and provider."""
        # 1. Start Browser
        # Pass session_path if available to load cookies
        page = self.browser_manager.start(headless=self.headless, session_path=self.session_path)
        
        # Grant clipboard permissions for response extraction
        self.browser_manager.context.grant_permissions(["clipboard-read", "clipboard-write"])
        
        # 2. Initialize Provider
        if self.provider_name.lower() == "chatgpt":
            # Pass config for selectors if needed
            self.provider = ChatGPTProvider(page, config=self.config, on_otp_required=self.on_otp_required)
        else:
            raise NotImplementedError(f"Provider {self.provider_name} not supported.")
            
        # 3. Check Auth / Auto-Login
        if not self.browser_manager.is_authenticated(self.provider.URL, self.provider.SEL_PROFILE_BTN):
            logger.info("Not authenticated. Initiating login...")
            
            # Prioritize passed credentials, fallback to Config/Env vars
            creds = self.credentials or Config.get_credentials(self.provider_name)
            
            if not creds.get("email") or not creds.get("password"):
                raise SetupError("Credentials not found. Pass them to Automator() or set environment variables (CHATGPT_EMAIL, CHATGPT_PASSWORD).")
            
            self.provider.login(creds)
            
            # Save session if path provided
            if self.session_path:
                self.browser_manager.save_session(self.session_path)
                logger.info(f"Session saved to {self.session_path}")
        else:
            logger.info("Session authenticated.")

    def process_prompt(self, prompt: str) -> str:
        """
        Send a single prompt and get the response.
        """
        if not self.provider:
            raise SetupError("Provider not initialized.")
        return self.provider.send_prompt(prompt)

    def process_chain(self, prompts: List[Union[str, Callable[[str], str]]]) -> List[str]:
        """
        Process a chain of prompts. 
        Supports string formatting with {} (previous response injected) or callables.
        """
        responses = []
        last_response = ""
        
        for i, prompt_item in enumerate(prompts):
            current_prompt = ""
            
            if callable(prompt_item):
                current_prompt = prompt_item(last_response)
            elif isinstance(prompt_item, str):
                # If it's a string, try to format it with the last response if it contains placeholders
                # We use a specific placeholder {{previous}} to avoid accidental formatting of user code
                # But we also support {} for backward compatibility if it's simple
                
                if "{{previous}}" in prompt_item:
                     current_prompt = prompt_item.replace("{{previous}}", last_response)
                elif "{}" in prompt_item:
                    # Basic check to avoid formatting JSON or Python dicts
                    # If the string looks like code, we might skip this or warn?
                    # For now, we'll just try format, but this is risky as noted in review.
                    # Better approach: Only format if it's clearly a placeholder.
                    try:
                        current_prompt = prompt_item.format(last_response)
                    except ValueError:
                        # If format fails (e.g. mismatched braces), treat as literal
                        current_prompt = prompt_item
                elif "{{}}" in prompt_item: # Support legacy double braces
                    current_prompt = prompt_item.replace("{{}}", last_response)
                else:
                    current_prompt = prompt_item
            
            logger.info(f"Processing prompt {i+1}/{len(prompts)}...")
            response = self.process_prompt(current_prompt)
            responses.append(response)
            last_response = response
            
        return responses

    def close(self):
        """Clean up resources."""
        self.browser_manager.stop()
