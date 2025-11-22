import { Automator } from './src';

async function main() {
    console.log("--- Starting Verification (Node.js) ---");



    const bot = new Automator(
        "chatgpt",
        false,
        {
            email: "email@example.com",
            password: "password",
            method: "google"
        }
    ); // Headless false for verification

    try {
        console.log("Initializing Automator...");
        await bot.init();

        // Test 1: Single Prompt
        console.log("\n[Test 1] Single Prompt");
        const prompt = "What is 5 + 5? Answer with just the number.";
        const response = await bot.processPrompt(prompt);
        console.log(`Prompt: ${prompt}`);
        console.log(`Response: ${response}`);

        if (response.includes("10")) {
            console.log(">> Test 1 PASSED");
        } else {
            console.log(">> Test 1 FAILED (Unexpected response)");
        }

        // Test 2: Chained Prompt
        console.log("\n[Test 2] Chained Prompt");
        const chain = [
            "Generate a random fruit name.",
            "What is the color of {}?"
        ];
        const responses = await bot.processChain(chain);
        console.log(`Chain Responses: ${JSON.stringify(responses)}`);

        if (responses.length === 2 && responses[1].length > 2) {
            console.log(">> Test 2 PASSED");
        } else {
            console.log(">> Test 2 FAILED");
        }

    } catch (e) {
        console.error(`ERROR during verification: ${e}`);
    } finally {
        await bot.close();
        console.log("\n--- Verification Complete ---");
    }
}

main();
