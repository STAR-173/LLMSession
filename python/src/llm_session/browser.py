import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, BrowserContext, Page, Playwright
import appdirs

from .exceptions import SetupError

class BrowserManager:
    """Manages the Playwright browser instance and persistent context."""

    def __init__(self, app_name: str = "LLMSession"):
        self.user_data_dir = Path(appdirs.user_data_dir(app_name, appauthor=False))
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def ensure_dependencies_installed(self):
        """
        Check if Playwright browsers are installed.
        We no longer auto-install to avoid side effects.
        """
        # We can't easily check without running, but we can try-catch the launch.
        # If launch fails, we assume it's missing and tell the user what to do.
        pass

    def start(self, headless: bool = True, session_path: Optional[str] = None) -> Page:
        """
        Start the browser with a persistent context.
        
        Args:
            headless: Whether to run in headless mode.
            session_path: Path to a storageState.json file to load cookies/session.
            
        Returns:
            Page: The default page of the context.
        """
        if not self.user_data_dir.exists():
            self.user_data_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.playwright = sync_playwright().start()
        except Exception as e:
             raise SetupError(f"Failed to start Playwright. Make sure it is installed: {e}")
        
        # Launch persistent context
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        
        try:
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars",
                    "--exclude-switches=enable-automation",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding"
                ]
            )
        except Exception as e:
            raise SetupError(f"Failed to launch browser. You may need to run 'playwright install': {e}")
        
        # Load session if provided (though persistent context usually handles this, 
        # explicit loading can be useful if we want to inject a specific state file into the persistent dir)
        # Note: launch_persistent_context uses the user_data_dir, so it persists automatically.
        # If session_path is provided, we might want to overwrite or merge?
        # Playwright doesn't have a direct 'load_storage_state' for persistent context after launch easily
        # without just relying on the dir. 
        # However, if the user wants to *import* a session, we can try to deserialize and add cookies.
        # For now, we'll rely on the persistent context behavior, but if a path is given, we assume
        # the user wants to use THAT state. 
        # Actually, launch_persistent_context doesn't take 'storageState' arg like launch().
        # So we rely on user_data_dir. 
        # If session_path is passed, we can manually add cookies.
        
        if len(self.context.pages) > 0:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
            
        return self.page

    def save_session(self, path: str):
        """Save the current session (cookies/storage) to a file."""
        if self.context:
            self.context.storage_state(path=path)

    def load_session(self, path: str):
        """
        Load a session from a file. 
        Note: For persistent context, this is best done by just using the same user_data_dir.
        But we can manually add cookies if needed.
        """
        # Not fully implemented for persistent context as it handles its own state.
        pass

    def stop(self):
        """Close the browser context and playwright."""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

    def is_authenticated(self, check_url: str, check_selector: str) -> bool:
        """
        Check if the session is authenticated by navigating to a URL and checking for an element.
        
        Args:
            check_url: URL to visit.
            check_selector: Selector that indicates a logged-in state.
            
        Returns:
            bool: True if authenticated.
        """
        if not self.page:
            raise SetupError("Browser not started.")
        
        try:
            self.page.goto(check_url, wait_until="domcontentloaded")
            # Wait a bit for dynamic content, but not too long
            try:
                self.page.wait_for_selector(check_selector, timeout=5000)
                return True
            except:
                return False
        except Exception as e:
            print(f"Auth check failed: {e}")
            return False
