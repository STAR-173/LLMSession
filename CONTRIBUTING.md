# Contributing to LLMSession

Thank you for your interest in contributing to **LLMSession**! This project is a monorepo containing both the Python and Node.js implementations. We welcome contributions to either (or both) parts of the library.

## 1. Project Structure

*   **`python/`**: Contains the Python source code and packaging config.
*   **`node/`**: Contains the TypeScript source code and NPM config.

Please ensure you are working in the correct subdirectory for your changes.

## 2. Python Development

### Setup
1.  Navigate to the python directory: `cd python`
2.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # or
    .\venv\Scripts\activate   # Windows
    ```
3.  Install the package in **Editable Mode**:
    ```bash
    pip install -e .
    ```
    *This allows you to modify code in `src/` and test it immediately without reinstalling.*

### Testing
We use a manual verification script to test the full flow (Browser launch -> Auth -> Prompt).
```bash
python verify_flow.py
```
*Tip: You can modify `verify_flow.py` to use `headless=False` to watch the bot work.*

## 3. Node.js Development

### Setup
1.  Navigate to the node directory: `cd node`
2.  Install dependencies:
    ```bash
    npm install
    ```

### Building
Since this is a TypeScript project, you must compile the code.
*   **One-off build**:
    ```bash
    npm run build
    ```
*   **Watch mode (Recommended for Dev)**:
    ```bash
    npx tsc -w
    ```
    *Keep this running in a separate terminal to auto-compile changes.*

### Testing
To run the verification flow using `ts-node` (skips build step) or the compiled dist:
```bash
# Run directly from TypeScript source
npx ts-node verify_flow.ts
```

## 4. Safety Warning (Credentials)

To test changes, you will likely need to put real credentials into `verify_flow.py` or `verify_flow.ts`.

> [!CAUTION]
> **NEVER commit files containing your real passwords.**
> If you modify the verification scripts with real credentials, please revert those changes before pushing, or ensure they are ignored.

## 5. Pull Request Process

1.  **Fork & Clone**: Fork the repo and clone it locally.
2.  **Branch**: Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  **Code**: Implement your changes.
    *   **Python**: Adhere to PEP 8.
    *   **Node**: Adhere to standard ESLint/Prettier conventions.
4.  **Verify**: Run the verification scripts in both languages if your change affects shared logic (like selectors).
5.  **Commit**: Use descriptive commit messages.
6.  **Push & PR**: Push to your fork and open a Pull Request against `main`.

## 6. Adding New Selectors

If you are fixing a broken selector because ChatGPT updated their UI:
1.  Update `python/src/llm_session/providers/chatgpt.py`
2.  Update `node/src/providers/ChatGPT.ts`
3.  **Please update both** if possible to keep the libraries in sync.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.