import os
import sys
from pathlib import Path

# Add src to path so we can import without installing
sys.path.append(str(Path(__file__).parent / "src"))

from llm_session import Automator

def main():
    print("--- Starting Verification ---")

    try:
        # Initialize Automator (this handles setup & auth)
        # We use headless=False for the first run to see what's happening, or let the user decide.
        # But the requirement says "non-interactive", so we should default to True.
        # However, for verification, seeing it is nice. Let's stick to the config default (True) 
        # but maybe allow override.
        print("Initializing Automator...")
        bot = Automator(
            headless=False,
            provider="chatgpt", 
            credentials={
                "email": "test@example.com", 
                "password": "password",
                "method": "google"
            }
        )

        # Test 2: Chained Prompt
        print("\n[Test 2] Chained Prompt")
        chain = [
            "Generate a random color name.",
            "Write a short poem about {}."
        ]
        responses = bot.process_chain(chain)
        print(f"Chain Responses: {responses}")
        
        if len(responses) == 2 and len(responses[1]) > 10:
            print(">> Test 2 PASSED")
        else:
            print(">> Test 2 FAILED")

        bot.close()
        print("\n--- Verification Complete ---")

    except Exception as e:
        print(f"\nERROR during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
