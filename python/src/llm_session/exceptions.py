class LLMAutomatorError(Exception):
    """Base exception for LLM Automator."""
    pass

class SetupError(LLMAutomatorError):
    """Raised when setup or installation fails."""
    pass

class AuthenticationError(LLMAutomatorError):
    """Raised when authentication fails."""
    pass

class PromptError(LLMAutomatorError):
    """Raised when prompt processing fails."""
    pass

class SelectorError(LLMAutomatorError):
    """Raised when a UI element cannot be found."""
    pass

class OTPRequiredError(LLMAutomatorError):
    """Raised when OTP is required but no handler is provided."""
    pass
