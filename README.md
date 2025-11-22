# LLMSession

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A zero-configuration tool to automate interactions with web-based LLM providers (currently ChatGPT). It handles authentication, session persistence, and chained prompt execution programmatically.

## Features
- **Zero-Config Setup**: Automatically handles browser binaries via Playwright.
- **Session Persistence**: Reuses cookies/storage for subsequent runs (no need to login every time).
- **Cross-Language Sharing**: Sessions are shared between Python and Node.js environments automatically.
- **Smart OTP Handling**: Supports non-blocking callbacks for 2FA/OTP challenges.
- **Resilient**: Allows custom CSS selectors to adapt to UI changes without updating the library.

## Prerequisites
You must set the following environment variables, or pass them directly to the constructor:
- `CHATGPT_EMAIL`
- `CHATGPT_PASSWORD`
- `CHATGPT_GOOGLE_LOGIN` (Optional: set to "true" if using Google Auth. *Note: Google Auth is experimental and may require manual intervention.*)

## Disclaimer
> [!WARNING]
> **Cloudflare/Bot Detection**: Automated interactions with ChatGPT are subject to high-security bot detection (Cloudflare). This library uses standard browser automation and may be blocked. For production reliability, please use the Official OpenAI API.

This tool automates a third-party web interface. It is subject to breakage if the target website changes its DOM structure. Use responsibly and in accordance with the provider's Terms of Service.

---

## Python Usage

### Installation
```bash
pip install llm-session
```

### Quick Start
```python
import logging
from llm_session import Automator

# 1. Configure Standard Logging
logging.basicConfig(level=logging.INFO)

# 2. Define OTP Callback (Optional, but recommended for headless envs)
def my_otp_handler():
    # In production, you might fetch this from an email API
    return input("Enter OTP Code sent to email: ")

# 3. Initialize
bot = Automator(
    provider="chatgpt",
    headless=False,  # Set to True for production (CURRENTLY ONLY WORKS WITH headless=False)
    credentials={
        "email": "your_email@example.com", 
        "password": "your_password",
        "method": "email" # or "google"
    },
    on_otp_required=my_otp_handler
)

# 4. Single Prompt
print(bot.process_prompt("Hello, world!"))

# 5. Chained Prompt (Inject previous response)
chain = [
    "Write a haiku about Python.",
    "Translate this haiku to Spanish: {{previous}}"
]
responses = bot.process_chain(chain)
print(responses)

bot.close()
```

---

## Node.js Usage

### Installation
```bash
npm install llm-session
```

### Quick Start
```typescript
import { Automator } from 'llm-session';

async function main() {
    // 1. Define OTP Callback
    const onOtpRequired = async () => {
        console.log("Please check your email for code.");
        // Return code from your logic here
        return "123456"; 
    };

    // 2. Initialize
    const bot = new Automator(
        "chatgpt", 
        false, // headless
        {
            email: "your_email@example.com",
            password: "your_password"
        },
        undefined, // sessionPath (optional)
        {
            onOtpRequired: onOtpRequired,
            // Optional: Inject your own logger (e.g., Winston, Pino)
            // logger: myLoggerInstance 
        }
    );
    
    try {
        await bot.init();

        const response = await bot.processPrompt("Hello from Node.js!");
        console.log(response);

    } finally {
        await bot.close();
    }
}
main();
```

---

## Advanced Configuration (Resilience)

Websites change their layout often. If ChatGPT updates their CSS class names, you don't need to wait for a package update. You can inject your own selectors during initialization.

**Python:**
```python
bot = Automator(
    provider="chatgpt", 
    config={
        "selectors": {
            "textarea": "#new-prompt-id",
            "send_btn": ".new-send-button-class",
            "assistant_msg": ".new-message-wrapper"
        }
    }
)
```

**Node.js:**
```typescript
const bot = new Automator("chatgpt", true, undefined, undefined, {
    selectors: {
        textarea: "#new-prompt-id",
        send_btn: ".new-send-button-class"
    }
});
```

## Session Management
This library stores browser cookies and local storage in your OS's standard user data directory (e.g., `%LOCALAPPDATA%/LLMSession` on Windows, `~/.local/share/LLMSession` on Linux).

*   **Cross-Language:** If you login using the Python script, the Node.js script will automatically detect the existing session and skip login (and vice-versa).
*   **Persistence:** Sessions persist across reboots.

## Contributing
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to build the project locally.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.