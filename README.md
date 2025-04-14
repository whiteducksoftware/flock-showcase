# 🚀 Flock Showcase: Examples & Projects 🚀

<p align="center">
  <!-- Placeholder for your Flock Logo/Banner - Replace URL -->
  <img alt="Flock Banner" src="https://raw.githubusercontent.com/whiteducksoftware/flock/master/docs/assets/images/flock.png" width="600">
</p>
<p align="center">
  <!-- Add relevant badges if you have them -->
  <img alt="Python Version" src="https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python">
  <a href="https://github.com/whiteducksoftware/flock" target="_blank"><img alt="Core Repo" src="https://img.shields.io/badge/Core%20Repo-flock-brightgreen?style=for-the-badge&logo=github"></a>
  <!-- <a href="YOUR_LICENSE_URL" target="_blank"><img alt="License" src="https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge"></a> -->
</p>

---

**Welcome to the Flock Showcase!** This repository is the official collection of examples, guides, and mini-projects demonstrating the capabilities of the [Flock Framework](https://github.com/whiteducksoftware/flock).

Flock is a declarative AI agent framework designed to make building robust, scalable, and maintainable agent systems easier by focusing on *what* you want to achieve, rather than getting lost in complex prompt engineering.

This showcase will guide you from your very first simple agent ("Hello Flock!") all the way to building more complex, multi-agent applications and utilizing advanced features.

## ✨ Why Flock?

Flock offers a different approach to agent development:

*   **Declarative:** Define agents by their inputs, outputs, tools, and descriptions. Let Flock handle the LLM interaction details.
*   **Robust:** Built with production in mind, including optional Temporal integration for fault tolerance.
*   **Modular:** Extend agent capabilities easily with pluggable Modules, Evaluators, and Routers.
*   **Type-Safe:** Leverage Pydantic and Python type hints for clear contracts and validation.
*   **Less Prompt Fuss:** Spend more time designing your system and less time tweaking brittle mega-prompts.

Dive into the [Core Flock Documentation](https://whiteducksoftware.github.io/flock/) for a deeper understanding of the concepts.

## 📂 Repository Structure

The examples are organized progressively to help you learn step-by-step:

*   **`01-getting-started/`**: The absolute basics. Run your first agent in minutes and see the declarative approach in action (e.g., *Wacky Title Generator*, *Alien Pet Profile Creator*).
*   **`02-core-concepts/`**: Understand fundamental Flock ideas with simple, focused examples (e.g., *Declarative Haiku Bot*, *Pydantic Fantasy Character Sheet*, *Simple Recipe->Shopping List Chain*).
*   **`03-intermediate-guides/`**: Tackle common practical tasks and combine core concepts (e.g., *Custom Dad Joke Tool*, *Customer Support Router*, *Basic RAG Bot*, *Saving/Loading Flocks*).
*   **`04-advanced-features/`**: Explore powerful capabilities like batch processing, evaluation, streaming, hierarchical memory, and API/CLI interactions (e.g., *Social Post Variations*, *Evaluating RAG*, *Live Story Stream*).
*   **`05-full-projects/`**: See larger, multi-file examples integrating multiple Flock features into mini-applications (e.g., *AI Dungeon Master's Assistant*, *Codebase Documenter*, *Emoji Adventure Game*).
*   **`cookbook/`**:  Small, focused code snippets for specific patterns or configurations.

Each numbered directory contains a `README.md` explaining the concepts covered in that section.

## 🚀 Getting Started

Ready to take flight? Follow these steps:

1.  **Prerequisites:**
    *   Python 3.10 or higher.
    *   `git` installed.
    *   `pip` or preferably `uv` ([Install uv](https://docs.astral.sh/uv/getting-started/installation/)) for package management.

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/whiteducksoftware/flock-showcase.git
    cd flock-showcase
    ```

3.  **Set up Virtual Environment (without `uv`):**
    *   Using standard `venv`:
        ```bash
        python -m venv .venv
        source .venv/bin/activate  # Linux/macOS
        # .\.venv\Scripts\activate  # Windows (cmd)
        # .\.venv\Scripts\Activate.ps1 # Windows (PowerShell)
        ```

4.  **Install Dependencies:**
    ```bash
    # Using uv (recommended)
    uv sync

    # Using pip
    pip install -r requirements.txt
    ```
    *(`requirements.txt` should ideally include `flock-core[all]` and any other specific libraries used in the examples like `pandas`, `datasets`, `nltk`, etc.)*

5.  **Configure API Keys:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   **IMPORTANT:** Open the `.env` file in your text editor and add your API keys for the LLM providers (OpenAI, Anthropic, Google Gemini, etc.) and any tools (Tavily, GitHub PAT, Azure Search) used by the examples you want to run. Flock uses `litellm`, so refer to their documentation for required environment variable names.

## ▶️ Running Examples

1.  **Activate your virtual environment** (if not already active):
    ```bash
    source .venv/bin/activate # Or your specific activation command
    ```
2.  **Navigate** to the directory of the example you want to run:
    ```bash
    cd 01-getting-started/
    ```
3.  **Execute** the Python script:
    ```bash
    python 01-hello-flock.py

    # or

    uv run 01-hello-flock.py
    ```
4.  **Observe!** See Flock in action. Remember that examples using specific tools or LLMs require the corresponding API key to be set in your `.env` file.

## 💡 Examples Overview

*   **01 Getting Started:** Your first agent, basic typed output, simple tool use.
*   **02 Core Concepts:** Declarative approach, Pydantic types, basic chaining, multi-tool agents, modules, context.
*   **03 Intermediate Guides:** Custom tools, dynamic routing (LLM/Agent), basic RAG, knowledge graph memory, saving/loading.
*   **04 Advanced Features:** Batch processing, agent evaluation, streaming, hierarchical memory, API/CLI interaction.
*   **05 Full Projects:** Complete mini-applications demonstrating integrated Flock usage.
*   **Cookbook:** Quick solutions for specific tasks.

## 🤝 Contributing

Contributions are welcome! If you have ideas for new examples, improvements to existing ones, or find bugs, please feel free to:

*   Open an [Issue](https://github.com/YOUR_USERNAME/flock-showcase/issues).
*   Submit a [Pull Request](https://github.com/YOUR_USERNAME/flock-showcase/pulls).

Please follow standard coding practices and ensure examples are clear and runnable.

## 📜 License

This showcase repository is licensed under the [MIT License](LICENSE). <!-- Update LICENSE if different -->

## 🔗 Links

*   **Flock Core Repository:** [https://github.com/whiteducksoftware/flock](https://github.com/whiteducksoftware/flock)
*   **Flock Documentation:** [https://whiteducksoftware.github.io/flock/](https://whiteducksoftware.github.io/flock/)
*   **white duck GmbH:** [https://whiteduck.de](https://whiteduck.de)

---

Happy Flocking! 🐦‍⬛💨