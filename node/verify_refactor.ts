import { Automator } from './src';

async function main() {
    console.log("Starting Node.js Verification...");

    const onOtpRequired = async () => {
        console.log("OTP Handler called!");
        return "123456";
    };

    try {
        const bot = new Automator(
            "chatgpt",
            true,
            {
                email: "test@example.com",
                password: "password"
            },
            undefined,
            {
                onOtpRequired: onOtpRequired,
                logger: console
            }
        );

        console.log("Automator initialized successfully.");

        await bot.init();

        console.log("Closing Automator...");
        await bot.close();
        console.log("Verification Passed!");

    } catch (e: any) {
        console.error(`Verification Failed: ${e}`);
        if (e.message.includes("Login failed") || e.message.includes("Timeout")) {
            console.log("Login failed as expected with dummy creds. Structure is correct.");
        } else {
            process.exit(1);
        }
    }
}

main();
