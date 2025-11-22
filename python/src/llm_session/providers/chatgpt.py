import time
import logging
from typing import Optional, Callable
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from .base import LLMProvider
from ..exceptions import AuthenticationError, SelectorError, PromptError, OTPRequiredError

logger = logging.getLogger(__name__)

class ChatGPTProvider(LLMProvider):
    """ChatGPT implementation."""

    URL = "https://chatgpt.com/"  # Changed to root URL
    # LOGIN_URL is no longer used directly, we navigate to URL then click login

    # Default Selectors
    DEFAULT_SELECTORS = {
        # New Login Flow Selectors
        "landing_login_btn": '[data-testid="login-button"]',
        "login_google_btn": 'button:has-text("Continue with Google")',
        "email_input": '#email', # ID is robust
        "email_continue_btn": 'button[type="submit"]', # The email "Continue" is type="submit", Google is type="button"
        
        # Password Step (Likely remains similar, but using generic fallback if needed)
        "password_input": 'input[name="password"]', # Sometimes 'current-password' or just 'password'
        "password_continue_btn": 'button[type="submit"]', # Usually same submit button logic
        
        # Post-Login
        "profile_btn": '[data-testid="accounts-profile-button"]',
        "textarea": '#prompt-textarea',
        "send_btn": 'button[data-testid="send-button"]',
        "stop_btn": 'button[data-testid="stop-button"]',
        "assistant_msg": 'div[data-message-author-role="assistant"]',
        
        # Dialogs
        "upsell_maybe_later": 'button:has-text("Maybe later")',
        "temp_chat_continue": 'button:has-text("Continue")',
        
        # OTP
        "otp_input": 'input[name="code"]',
        "otp_validate": 'button[type="submit"]' # Usually submit button
    }

    def __init__(self, page: Page, config: Optional[dict] = None, on_otp_required: Optional[Callable[[], str]] = None):
        super().__init__(page)
        self.config = config or {}
        self.on_otp_required = on_otp_required
        self.selectors = self.DEFAULT_SELECTORS.copy()
        
        # Override selectors from config
        if "selectors" in self.config:
            self.selectors.update(self.config["selectors"])
            
        # Map selectors to instance variables for easy access
        self.SEL_PROFILE_BTN = self.selectors["profile_btn"]
        self.SEL_TEXTAREA = self.selectors["textarea"]
        self.SEL_SEND_BTN = self.selectors["send_btn"]
        self.SEL_STOP_BTN = self.selectors["stop_btn"]

    def login(self, credentials: dict) -> bool:
        logger.info("Starting login process...")
        # 1. Go to main page
        self.page.goto(self.URL)
        
        # 2. Handle Upsells/Dialogs immediately upon landing (as requested)
        self.handle_dialogs()
        
        # 3. Check if already logged in (Profile button exists)
        try:
            self.page.wait_for_selector(self.selectors["profile_btn"], timeout=3000)
            logger.info("Already logged in.")
            return True
        except:
            pass

        # 4. Click the Landing Page "Log in" button
        try:
            logger.info("Clicking 'Log in' from landing page...")
            self.page.click(self.selectors["landing_login_btn"])
        except Exception as e:
            raise SelectorError(f"Could not find Login button on landing page: {e}")

        email = credentials.get("email")
        password = credentials.get("password")
        method = credentials.get("method", "email") # Default to email
        
        if not email or not password:
            raise AuthenticationError("Email and password are required.")

        try:
            if method == "google":
                logger.info("Logging in via Google...")
                # Wait for the modal/redirect to load the Google button
                self.page.wait_for_selector(self.selectors["login_google_btn"])
                self.page.click(self.selectors["login_google_btn"])
                
                # Google Email
                logger.info("Entering Google email...")
                self.page.wait_for_selector('input[type="email"]')
                self.page.fill('input[type="email"]', email)
                self.page.click('button:has-text("Next")') # Generic "Next" button
                
                # Google Password
                logger.info("Entering Google password...")
                self.page.wait_for_selector('input[type="password"]', state="visible")
                self.page.fill('input[type="password"]', password)
                self.page.click('button:has-text("Next")')
                
            else:
                # Email Step
                logger.info("Entering email...")
                self.page.wait_for_selector(self.selectors["email_input"])
                self.page.fill(self.selectors["email_input"], email)
                
                # Click Continue (using type="submit" to differentiate from Google button)
                self.page.click(self.selectors["email_continue_btn"])
                
                # Password Step
                logger.info("Entering password...")
                # Wait for password field to appear (animation)
                self.page.wait_for_selector(self.selectors["password_input"])
                self.page.fill(self.selectors["password_input"], password)
                self.page.click(self.selectors["password_continue_btn"])
            
            # Wait for login to complete OR OTP check
            logger.info("Waiting for authentication or OTP...")
            
            try:
                # Loop to check for success or OTP
                for _ in range(30): # 30 seconds max
                    if self.page.is_visible(self.selectors["profile_btn"]):
                        logger.info("Login successful.")
                        return True
                    
                    if self.page.is_visible(self.selectors["otp_input"]):
                        logger.warning("OTP verification required.")
                        
                        if not self.on_otp_required:
                            raise OTPRequiredError("OTP required but no on_otp_required callback provided.")
                        
                        otp_code = self.on_otp_required()
                        
                        self.page.fill(self.selectors["otp_input"], otp_code)
                        self.page.click(self.selectors["otp_validate"])
                        logger.info("OTP submitted. Waiting for authentication...")
                        self.page.wait_for_selector(self.selectors["profile_btn"], timeout=30000)
                        logger.info("Login successful.")
                        return True
                    
                    time.sleep(1)
                
                raise TimeoutError("Login timed out.")
                
            except Exception as e:
                raise e
                
        except Exception as e:
            logger.error(f"Login/OTP failed: {e}")
            self.page.screenshot(path="login_failure.png")
            raise AuthenticationError(f"Login failed: {e}")

    def handle_dialogs(self):
        """Dismiss known dialogs."""
        # Try Go Upsell
        try:
            if self.page.is_visible(self.selectors["upsell_maybe_later"]):
                logger.debug("Dismissing 'Try Go' upsell...")
                self.page.click(self.selectors["upsell_maybe_later"])
                # Wait briefly for animation
                self.page.wait_for_timeout(500)
        except:
            pass
            
        # Temporary Chat
        try:
            if self.page.is_visible('h2:has-text("Temporary Chat")'):
                logger.debug("Dismissing 'Temporary Chat' dialog...")
                self.page.click(self.selectors["temp_chat_continue"])
                self.page.wait_for_timeout(500)
        except:
            pass

    def send_prompt(self, prompt: str) -> str:
        # 1. Handle Dialogs first
        self.handle_dialogs()
        
        # 2. Enter Prompt
        try:
            self.page.wait_for_selector(self.selectors["textarea"])
            self.page.fill(self.selectors["textarea"], prompt)
            
            # 3. Click Send
            self.page.wait_for_selector(self.selectors["send_btn"])
            # Ensure it's enabled
            if self.page.is_disabled(self.selectors["send_btn"]):
                self.page.wait_for_timeout(500)
            
            self.page.click(self.selectors["send_btn"])
            
        except Exception as e:
            raise PromptError(f"Failed to send prompt: {e}")

        # 4. Wait for generation to finish
        logger.info("Waiting for response...")
        try:
            # Wait for Stop button to appear (generation started)
            self.page.wait_for_selector(self.selectors["stop_btn"], timeout=5000)
            # Wait for Stop button to disappear (generation finished)
            self.page.wait_for_selector(self.selectors["stop_btn"], state="hidden", timeout=120000) # 2 min timeout
        except PlaywrightTimeoutError:
            if self.page.is_visible(self.selectors["send_btn"]):
                pass # It's done
            else:
                raise PromptError("Timeout waiting for response generation.")

        # 5. Extract Response
        try:
            # Wait for the assistant message to be present
            self.page.wait_for_selector(self.selectors["assistant_msg"], timeout=5000)
            
            assistant_msgs = self.page.query_selector_all(self.selectors["assistant_msg"])
            if not assistant_msgs:
                raise SelectorError("No assistant messages found.")
            
            last_msg = assistant_msgs[-1]
            
            # Extract text from the markdown container
            markdown_div = last_msg.query_selector('.markdown')
            if markdown_div:
                return markdown_div.inner_text()
            else:
                return last_msg.inner_text()
            
        except Exception as e:
            raise PromptError(f"Failed to extract response: {e}")