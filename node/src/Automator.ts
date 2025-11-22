import { BrowserManager } from './BrowserManager';
import { ChatGPTProvider } from './providers/ChatGPT';

export interface LoggerInterface {
    info(message: string): void;
    warn(message: string): void;
    error(message: string): void;
    debug(message: string): void;
}

export interface AutomatorConfig {
    selectors?: Record<string, string>;
    logger?: LoggerInterface;
    onOtpRequired?: () => Promise<string>;
}

export class Automator {
    private browserManager!: BrowserManager;
    private provider: ChatGPTProvider | null = null;
    private providerName: string;
    private headless: boolean;
    private credentials?: { email?: string, password?: string, method?: string };
    private sessionPath?: string;
    private config: AutomatorConfig;
    private logger: LoggerInterface;

    constructor(
        provider: string = "chatgpt",
        headless: boolean = true,
        credentials?: { email?: string, password?: string, method?: string },
        sessionPath?: string,
        config?: AutomatorConfig
    ) {
        this.providerName = provider;
        this.headless = headless;
        this.credentials = credentials;
        this.sessionPath = sessionPath;
        this.config = config || {};

        // Default logger to console if not provided
        this.logger = this.config.logger || console;
    }

    public async init(): Promise<void> {
        this.browserManager = new BrowserManager();
        // Pass sessionPath to start if we want to load cookies (though persistent context handles it, 
        // we might want to explicitly load a state file if provided)
        const page = await this.browserManager.start(this.headless, this.sessionPath);

        if (this.browserManager.context) {
            await this.browserManager.context.grantPermissions(["clipboard-read", "clipboard-write"]);
        }

        if (this.providerName === "chatgpt") {
            this.provider = new ChatGPTProvider(page, this.config.selectors, this.logger, this.config.onOtpRequired);
        } else {
            throw new Error(`Unknown provider: ${this.providerName}`);
        }

        // Check Auth / Auto-Login
        if (!await this.browserManager.isAuthenticated(this.provider.URL, this.provider.SEL_PROFILE_BTN)) {
            this.logger.info("Not authenticated. Initiating login...");

            // Credentials priority: Constructor args > Env vars
            const email = this.credentials?.email || process.env.CHATGPT_EMAIL;
            const password = this.credentials?.password || process.env.CHATGPT_PASSWORD;
            const method = this.credentials?.method || "email";

            if (!email || !password) {
                throw new Error("Credentials not provided. Set CHATGPT_EMAIL and CHATGPT_PASSWORD env vars or pass them to constructor.");
            }

            await this.provider.login({ email, password, method });

            if (this.sessionPath) {
                await this.browserManager.saveSession(this.sessionPath);
                this.logger.info(`Session saved to ${this.sessionPath}`);
            }
        } else {
            this.logger.info("Session authenticated.");
        }
    }

    public async processPrompt(prompt: string): Promise<string> {
        if (!this.provider) throw new Error("Provider not initialized. Call init() first.");
        return await this.provider.sendPrompt(prompt);
    }

    public async processChain(prompts: (string | ((prev: string) => string))[]): Promise<string[]> {
        const responses: string[] = [];
        let lastResponse = "";

        for (let i = 0; i < prompts.length; i++) {
            let currentPrompt = "";
            const promptItem = prompts[i];

            if (typeof promptItem === 'function') {
                currentPrompt = promptItem(lastResponse);
            } else {
                currentPrompt = promptItem;
                if (currentPrompt.includes("{}")) {
                    currentPrompt = currentPrompt.replace("{}", lastResponse);
                } else if (currentPrompt.includes("{{}}")) {
                    currentPrompt = currentPrompt.replace("{{}}", lastResponse);
                }
            }

            this.logger.info(`Processing prompt ${i + 1}/${prompts.length}...`);
            const response = await this.processPrompt(currentPrompt);
            responses.push(response);
            lastResponse = response;
        }

        return responses;
    }

    public async close(): Promise<void> {
        if (this.browserManager) {
            await this.browserManager.stop();
        }
    }
}
