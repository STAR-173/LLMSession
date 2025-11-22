import { chromium, BrowserContext, Page, Browser } from 'playwright';
import * as fs from 'fs-extra';
import * as path from 'path';
import * as os from 'os';
import { execSync } from 'child_process';

export class BrowserManager {
    private userDataDir: string;
    public context: BrowserContext | null = null;
    public page: Page | null = null;
    private browser: Browser | null = null;

    constructor() {
        // Simple user data dir implementation
        const appName = 'LLMSession';
        const home = os.homedir();
        // Windows: AppData/Local, Mac: Library/Application Support, Linux: .local/share
        const platform = process.platform;
        if (platform === 'win32') {
            this.userDataDir = path.join(process.env.LOCALAPPDATA || path.join(home, 'AppData', 'Local'), appName);
        } else if (platform === 'darwin') {
            this.userDataDir = path.join(home, 'Library', 'Application Support', appName);
        } else {
            // Linux: respect XDG_DATA_HOME environment variable (matches Python appdirs behavior)
            this.userDataDir = path.join(process.env.XDG_DATA_HOME || path.join(home, '.local', 'share'), appName);
        }
    }

    public ensureDependenciesInstalled(): void {
        // We no longer auto-install.
        // If launch fails, we throw an error telling the user to install.
    }

    public async start(headless: boolean = true, sessionPath?: string): Promise<Page> {
        fs.ensureDirSync(this.userDataDir);

        const userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36";
        const args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-infobars',
            '--exclude-switches=enable-automation',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding'
        ];

        try {
            this.context = await chromium.launchPersistentContext(this.userDataDir, {
                headless: headless,
                userAgent: userAgent,
                viewport: { width: 1280, height: 720 },
                args: args
            });
        } catch (e) {
            console.error(`Failed to launch browser: ${e}`);
            throw new Error("Failed to launch browser. Please ensure Playwright is installed via 'npx playwright install'.");
        }

        // If sessionPath is provided, we might want to load it.
        // Persistent context handles its own state in userDataDir.
        // If the user wants to inject a specific state, we can try to add cookies.
        if (sessionPath && fs.existsSync(sessionPath)) {
            try {
                const state = await fs.readJSON(sessionPath);
                if (state.cookies) {
                    await this.context.addCookies(state.cookies);
                }
                // We can't easily set localStorage/origins for persistent context after launch 
                // without navigating, but cookies are the main part.
            } catch (e) {
                console.error(`Failed to load session from ${sessionPath}: ${e}`);
            }
        }

        if (this.context.pages().length > 0) {
            this.page = this.context.pages()[0];
        } else {
            this.page = await this.context.newPage();
        }

        return this.page;
    }

    public async saveSession(path: string): Promise<void> {
        if (this.context) {
            await this.context.storageState({ path: path });
        }
    }

    public async stop(): Promise<void> {
        if (this.context) {
            await this.context.close();
        }
        if (this.browser) {
            await this.browser.close();
        }
    }

    public async isAuthenticated(url: string, selector: string): Promise<boolean> {
        if (!this.page) throw new Error("Browser not started");

        try {
            await this.page.goto(url, { waitUntil: 'domcontentloaded' });
            try {
                await this.page.waitForSelector(selector, { timeout: 5000 });
                return true;
            } catch {
                return false;
            }
        } catch (e) {
            // console.error(`Auth check failed: ${e}`);
            return false;
        }
    }
}
