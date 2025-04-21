# 02-core-concepts/01-declarative-vs-prompting.py
"""
Purpose: Demonstrate the difference between Flock's declarative approach
         and traditional detailed prompting for the same task.

Use Case: Haiku Bot 🌸 - Generate a haiku about a given theme.
"""


import litellm # For the traditional prompt example
from flock.core import Flock, FlockFactory
from rich.console import Console
from flock.cli.utils import print_header, print_subheader, print_success, print_warning

# --- Configuration ---
console = Console()
MODEL = "openai/gpt-4o" # Ensure OPENAI_API_KEY is set in your .env

# --- Flock (Declarative) Approach ---

def run_flock_haiku(theme: str):
    """Generates a haiku using the Flock declarative agent."""
    # 1. Create Flock Instance
    flock = Flock(name="haiku_flock", model=MODEL)

    print_subheader("Flock (Declarative) Approach")

    # 2. Define Agent Declaratively
    # Notice how we define WHAT we want (input, output, description)
    # We describe the output format but don't give explicit step-by-step instructions.
    haiku_agent = FlockFactory.create_default_agent(
        name="haiku_poet",
        description="A creative poet that generates haiku poems.",
        input="theme: str | The subject for the haiku",
        output="haiku: str | A three-line poem about the theme ideally following the 5-7-5 syllable structure.",
        temperature=0.7, # Let's make it a bit more creative
        use_cache=False, # Let's disable caching for this example so we get a fresh response each time
        wait_for_input=True # Let's wait for the user to press enter before continuing after this agent's run
    )
    flock.add_agent(haiku_agent)

    # 3. Run the Flock
    try:
        console.print(f"Theme: '{theme}'")
        console.print("Running Flock agent...")
        result = flock.run(
            start_agent=haiku_agent,
            input={"theme": theme}
        )
        print_success("Generated Haiku:")
        console.print(result.haiku, style="italic cyan") # Access the 'haiku_lines' output field
    except Exception as e:
        print_warning(f"Flock agent failed: {e}")
        print_warning("Ensure your API key is set in .env and the model is accessible.")

# --- Traditional Prompting Approach ---

def run_traditional_haiku(theme: str):
    """Generates a haiku using a detailed, traditional prompt."""
    print_subheader("Traditional Prompting Approach")

    # 1. Craft the Detailed Prompt
    # Notice how much more explicit instruction is needed compared to the
    # Flock agent's input/output/description fields.
    system_prompt = "You are a skilled poet specializing in writing concise and evocative haiku poems."
    user_prompt = f"""
Please write a haiku about the following theme: '{theme}'

Follow these rules strictly:
1. The haiku must have exactly three lines.
2. The first line must have 5 syllables.
3. The second line must have 7 syllables.
4. The third line must have 5 syllables.
5. The haiku must be directly related to the theme: '{theme}'.
6. Output ONLY the three lines of the haiku, with each line separated by a newline character. Do not include any other text, titles, or explanations.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # 2. Call the LLM directly (using litellm)
    try:
        console.print(f"Theme: '{theme}'")
        console.print("Running direct LLM call...")
        response = litellm.completion(
            model=MODEL,
            messages=messages,
            temperature=0.7, # Match temperature for fairness
            max_tokens=50 # Haikus are short
        )
        haiku_text = response.choices[0].message.content.strip()
        print_success("Generated Haiku:")
        console.print(haiku_text, style="italic magenta")
    except Exception as e:
        print_warning(f"Traditional prompt failed: {e}")
        print_warning("Ensure your API key is set in .env and the model is accessible.")


# --- Main Execution ---

if __name__ == "__main__":
    test_theme = "Snowy Morning"

    print_header(f"Haiku Generation Comparison: '{test_theme}'")

    run_flock_haiku(test_theme)

    console.print("\n" + "="*40 + "\n") # Separator

    run_traditional_haiku(test_theme)

    print_header("Comparison Complete")
    console.print("\nNotice how the Flock approach focuses on defining the desired input and output structure,")
    console.print("while the traditional approach requires detailed step-by-step instructions within the prompt itself.")

# --- YOUR TURN! ---
# 1. Change the `test_theme` variable (line 132) to something else (e.g., 'Silent Forest', 'City Rain'). Run the script again.
# 2. Modify the `output` string in the `haiku_agent` definition (line 45):
#    - Try changing the description: `output="haiku: str | A gloomy three-line poem..."`
#    - Try adding another output field: `output="haiku: str | ..., mood: str | The overall mood"`
#    (Remember to print the new 'mood' field in `run_flock_haiku` if you add it!)
# 3. Modify the detailed instructions in the `user_prompt` (line 90):
#    - Change the required syllable count rules.
#    - Ask it to *also* provide an explanation of the haiku after generating it.
# 4. Try generating a 'western' style poem, how much does the prompt need to change? 
# 5. Try adding a tool like `basic_tools.web_search_duckduckgo` to create poems about current events.
#
# See how changes differ between the declarative (Flock) and imperative (Traditional) methods!
# Which approach feels easier to modify and maintain for specific output structures?