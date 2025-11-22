import { Page } from 'playwright';
import { LoggerInterface } from '../Automator';

export class ChatGPTProvider {
    private page: Page;
    private selectors: Record<string, string>;
    private logger: LoggerInterface;
    private onOtpRequired?: () => Promise<string>;

    public static readonly URL = "https://chatgpt.com/";
    // LOGIN_URL removed in favor of navigating to root

    // Default Selectors
    private static readonly DEFAULT_SELECTORS = {
        // New Login Flow
        landing_login_btn: '[data-testid="login-button"]',
        login_google_btn: 'button:has-text("Continue with Google")',
        email_input: '#email',
        email_continue_btn: 'button[type="submit"]',

        password_input: 'input[name="password"]',
        password_continue_btn: 'button[type="submit"]',

        // Post Login
        profile_btn: '[data-testid="accounts-profile-button"]',
        textarea: '#prompt-textarea',
        send_btn: 'button[data-testid="send-button"]',
        stop_btn: 'button[data-testid="stop-button"]',
        assistant_msg: 'div[data-message-author-role="assistant"]',
        upsell_maybe_later: 'button:has-text("Maybe later")',
        temp_chat_continue: 'button:has-text("Continue")',
        otp_input: 'input[name="code"]',
        otp_validate: 'button[type="submit"]'
    };

    // Instance getters for compatibility with Automator
    public get URL() { return ChatGPTProvider.URL; }
    public get SEL_PROFILE_BTN() { return this.selectors.profile_btn; }

    constructor(page: Page, customSelectors?: Record<string, string>, logger?: LoggerInterface, onOtpRequired?: () => Promise<string>) {
        this.page = page;
        this.selectors = { ...ChatGPTProvider.DEFAULT_SELECTORS, ...customSelectors };
        this.logger = logger || console;
        this.onOtpRequired = onOtpRequired;
    }

    public async login(credentials: { email?: string, password?: string, method?: string }): Promise<boolean> {
        this.logger.info("Starting login process...");

        // 1. Go to main page
        await this.page.goto(ChatGPTProvider.URL);

        // 2. Handle Upsells immediately
        await this.handleDialogs();

        // 3. Check if already logged in
        try {
            await this.page.waitForSelector(this.selectors.profile_btn, { timeout: 3000 });
            this.logger.info("Already logged in.");
            return true;
        } catch { }

        // 4. Click Landing Login Button
        try {
            this.logger.info("Clicking 'Log in' from landing page...");
            await this.page.click(this.selectors.landing_login_btn);
        } catch (e) {
            throw new Error(`Could not find Login button on landing page: ${e}`);
        }

        const { email, password, method } = credentials;
        if (!email || !password) throw new Error("Email and password required");

        try {
            if (method === "google") {
                this.logger.info("Logging in via Google...");
                // Wait for modal/button
                await this.page.waitForSelector(this.selectors.login_google_btn);
                await this.page.click(this.selectors.login_google_btn);

                // Google Email
                this.logger.info("Entering Google email...");
                await this.page.waitForSelector('input[type="email"]');
                await this.page.fill('input[type="email"]', email);
                await this.page.click('#identifierNext >> button');

                // Google Password
                this.logger.info("Entering Google password...");
                await this.page.waitForSelector('input[type="password"]', { state: 'visible' });
                await this.page.fill('input[type="password"]', password);
                await this.page.click('#passwordNext >> button');

            } else {
                // Email Step
                this.logger.info("Entering email...");
                await this.page.waitForSelector(this.selectors.email_input);
                await this.page.fill(this.selectors.email_input, email);
                await this.page.click(this.selectors.email_continue_btn);

                // Password Step
                this.logger.info("Entering password...");
                await this.page.waitForSelector(this.selectors.password_input);
                await this.page.fill(this.selectors.password_input, password);
                await this.page.click(this.selectors.password_continue_btn);
            }

            this.logger.info("Waiting for authentication or OTP...");

            // Loop to check for success or OTP
            for (let i = 0; i < 30; i++) {
                if (await this.page.isVisible(this.selectors.profile_btn)) {
                    this.logger.info("Login successful.");
                    return true;
                }

                if (await this.page.isVisible(this.selectors.otp_input)) {
                    this.logger.warn("OTP verification required.");

                    if (!this.onOtpRequired) {
                        throw new Error("OTP required but no onOtpRequired callback provided.");
                    }

                    const otpCode = await this.onOtpRequired();

                    await this.page.fill(this.selectors.otp_input, otpCode);
                    await this.page.click(this.selectors.otp_validate);
                    this.logger.info("OTP submitted. Waiting for authentication...");
                    await this.page.waitForSelector(this.selectors.profile_btn, { timeout: 30000 });
                    this.logger.info("Login successful.");
                    return true;
                }

                await this.page.waitForTimeout(1000);
            }

            await this.page.waitForSelector(this.selectors.profile_btn, { timeout: 30000 });
            this.logger.info("Login successful.");
            return true;
        } catch (e) {
            this.logger.error(`Login failed: ${e}`);
            await this.page.screenshot({ path: 'login_failure_node.png' });
            throw e;
        }
    }

    private async handleDialogs(): Promise<void> {
        try {
            if (await this.page.isVisible(this.selectors.upsell_maybe_later)) {
                await this.page.click(this.selectors.upsell_maybe_later);
                await this.page.waitForTimeout(500);
            }
        } catch { }

        try {
            if (await this.page.isVisible('h2:has-text("Temporary Chat")')) {
                await this.page.click(this.selectors.temp_chat_continue);
                await this.page.waitForTimeout(500);
            }
        } catch { }
    }

    public async sendPrompt(prompt: string): Promise<string> {
        await this.handleDialogs();

        try {
            await this.page.waitForSelector(this.selectors.textarea);
            await this.page.fill(this.selectors.textarea, prompt);

            await this.page.waitForSelector(this.selectors.send_btn);
            if (await this.page.isDisabled(this.selectors.send_btn)) {
                await this.page.waitForTimeout(500);
            }
            await this.page.click(this.selectors.send_btn);
        } catch (e) {
            throw new Error(`Failed to send prompt: ${e}`);
        }

        this.logger.info("Waiting for response...");
        try {
            await this.page.waitForSelector(this.selectors.stop_btn, { timeout: 5000 });
            await this.page.waitForSelector(this.selectors.stop_btn, { state: 'hidden', timeout: 120000 });
        } catch (e) {
            if (await this.page.isVisible(this.selectors.send_btn)) {
                // Done
            } else {
                throw new Error("Timeout waiting for response generation.");
            }
        }

        // 5. Extract Response
        try {
            await this.page.waitForSelector(this.selectors.assistant_msg, { timeout: 5000 });

            const assistantMsgs = await this.page.$$(this.selectors.assistant_msg);
            if (!assistantMsgs || assistantMsgs.length === 0) {
                throw new Error("No assistant messages found.");
            }

            const lastMsg = assistantMsgs[assistantMsgs.length - 1];

            // Extract text from the markdown container
            const markdownDiv = await lastMsg.$('.markdown');
            if (markdownDiv) {
                return await markdownDiv.innerText();
            } else {
                return await lastMsg.innerText();
            }
        } catch (e) {
            this.logger.error(`Failed to extract response: ${e}`);
            throw e;
        }
    }
}