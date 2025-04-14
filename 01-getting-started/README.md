# 01: Getting Started - Your First Flight! 🚀

Welcome to Flock! This is the starting point for your journey into declarative AI agent development. The examples here are designed to get you up and running with the absolute basics as quickly as possible.

We'll create your very first agent, see how to define what it does without complex prompts, and run it to get structured output.

## Prerequisites

Before running these examples, please make sure you have:

1.  Cloned the `flock-showcase` repository.
2.  Set up your Python virtual environment (e.g., using `uv venv` or `python -m venv .venv`).
3.  Installed the required dependencies (`uv pip install -r requirements.txt` or `pip install -r requirements.txt`).
4.  **Crucially:** Copied `.env.example` to `.env` and filled in your API key(s) (e.g., `OPENAI_API_KEY`). These first examples primarily use an OpenAI model by default, but you can change the `MODEL` variable in the scripts.

Refer to the main [README.md](../../README.md) in the showcase root for detailed setup instructions.

## Examples in this Section

Here's what you'll find in this directory:

1.  **`01-hello-flock.py`**: The "Hello, World!" of Flock.
    *   **Concept:** Creates a minimal `Flock` instance and a simple `FlockAgent` using `FlockFactory.create_default_agent`.
    *   **Demonstrates:** Defining basic `input` and `output` fields as simple strings and running the agent with `flock.run()`.
    *   **Use Case:** *Wacky Presentation Idea Generator* - Takes a topic and generates a funny title, slide headers, and summaries. Check the "YOUR TURN!" comment in the code to experiment!

2.  **`02-inputs-and-outputs.py`**: Adding Detail and Control.
    *   **Concept:** Enhancing agent definitions with type hints and descriptions.
    *   **Demonstrates:** Using the `field_name: type | description` syntax within the `input` and `output` strings to provide more specific instructions to the LLM and enable better data validation. Shows how the agent's `description` field also guides its behavior. Uses helper utils for cleaner output printing.
    *   **Use Case:** *Fun Movie Concept Generator* - Takes a topic and generates a movie title (all caps), runtime, a wild synopsis, and a list of characters with descriptions.

3.  **`03-using-a-tool.py`**: Giving Agents Superpowers!
    *   **Concept:** Equipping agents with tools to perform actions beyond text generation.
    *   **Demonstrates:** Adding a pre-built tool (`basic_tools.get_web_content_as_markdown`) to an agent via the `tools=[...]` argument in `FlockFactory`. Also introduces `enable_rich_tables=True` and `output_theme` for styled console output using Rich.
    *   **Demonstrates:** Adding a second agent that uses a different tool.
    *   **Use Case 1:** *Webpage Analyzer* - Takes a URL, uses the tool to fetch the content as Markdown, and then analyzes it to extract the title, headings, entities, and classify the page type (news, blog, etc.).
    *   **Use Case 2:** *Celebrity Age Calculator* - Takes a celebrity name, uses the tool to fetch the content as Markdown, and then analyzes it to extract the title, headings, entities, and classify the page type (news, blog, etc.).

## ▶️ How to Run

1.  Make sure your virtual environment is activated (`source .venv/bin/activate` or similar).
2.  Ensure your `.env` file has the necessary API key (e.g., `OPENAI_API_KEY`).
3.  Navigate to this directory (`01-getting-started/`).
4.  Run the Python scripts:
    ```bash
    # Example 1
    python 01-hello-flock.py

    # Example 2
    python 02-inputs-and-outputs.py

    # Example 3 (Requires 'tavily-python' and 'markdownify' via requirements.txt)
    python 03-using-a-tool.py
    ```

## Key Takeaways

*   `Flock` is the main orchestrator.
*   `FlockAgent` defines what an agent does.
*   `FlockFactory.create_default_agent` is a quick way to start.
*   `input` and `output` strings declaratively define the agent's interface.
*   Type hints (`: str`) and descriptions (`| Some info`) in signatures guide the LLM.
*   `tools=[...]` adds capabilities to agents.
*   `flock.run()` executes the agent workflow.

## Next Steps

Now that you've run your first agents, head over to the `02-core-concepts` directory to dive deeper into the fundamental ideas behind Flock, such as Pydantic integration, agent chaining, and context management.

➡️ [**Explore Core Concepts (`../02-core-concepts/README.md`)**](../02-core-concepts/README.md)