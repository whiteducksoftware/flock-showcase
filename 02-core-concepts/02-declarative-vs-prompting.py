# 02-core-concepts/02-declarative-vs-prompting-alt.py
"""
Purpose: Demonstrate the difference between Flock's declarative approach
         and traditional detailed prompting for structured data extraction.

Use Case: News Article Analyzer 📰 - Extract structured data from news articles.

Highlights:
- The declarative approach defines the desired output structure using Pydantic models
- The traditional approach requires detailed instructions for each extraction step
- Both approaches extract the same information, but with different levels of complexity
- Shows how easy it is to modify and extend the declarative approach
"""

import os
from datetime import datetime
from typing import List, Literal, Optional

import litellm  # For the traditional prompt example
from flock.cli.utils import print_header, print_subheader, print_success, print_warning
from flock.core import Flock, FlockFactory
from flock.core.flock_registry import flock_type
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# --- Configuration ---
console = Console()
MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4o")
console.print(f"[grey50]Using model: {MODEL}[/grey50]")

# --- Sample News Article ---
SAMPLE_ARTICLE = """
Business Tech • 3 min read
OpenAI to remain under non-profit control in change of restructuring plans
By Reuters

Updated: 3:34 PM EDT, Mon May 5, 2025

Source: CNN

OpenAI said on Monday it would remain under the control of its nonprofit parent, while pushing ahead with plans to change the structure of its for-profit arm to allow more capital-raising to keep pace in the artificial-intelligence race.

The announcement follows a storm of criticism and legal challenges, including a high-profile lawsuit filed by rival Elon Musk, who has accused the company of straying from its founding mission to develop AI for the benefit of humanity.

“We made the decision for the nonprofit to stay in control after hearing from civic leaders and having discussions with the offices of the Attorneys General of California and Delaware,” the startup said in a blog post. It added that it would work with major backer Microsoft, regulators and newly appointed nonprofit commissioners to finalize the updated plan.

The company had outlined plans in December to revamp its structure to become a public benefit corporation, saying that would help it to “raise more capital than we’d imagined,” and remove the restrictions imposed on the startup by its current nonprofit parent.

The move had raised concerns about whether OpenAI would allocate its assets to the nonprofit arm fairly, and how the company would strike a balance between making a profit and generating social and public good as it develops AI.

On Monday, OpenAI said the nonprofit parent will control the public benefit corporation and become a big shareholder in it.

Nonprofits are created to serve the public good, while public benefit corporations typically offer more flexibility to pursue profit alongside social goals.

Bret Taylor, chairman of OpenAI’s board, said Monday’s announcement means the startup will continue to have a structure “extremely close” to the current one.

CEO Sam Altman described it as a compromise “that (works) well enough for investors that they’re happy to continue to fund us to a degree we think we will need.”

As the expensive pursuit of artificial general intelligence, or AI that surpasses human intelligence, heats up, OpenAI has been looking to make changes to attract further investment.

It said in March it would raise up to $40 billion in a new funding round led by SoftBank Group at a $300 billion valuation. The round was contingent on the AI firm transitioning to for-profit status by the end of the year.

SoftBank and Microsoft did not immediately respond to requests for comment.

Some analysts said the move could hamper the startup’s ability to raise capital as aggressively as it could have without the nonprofit control.

“The nonprofit status significantly reduces OpenAI’s ability to raise capital, as investors would want to be able to generate a return on their investment, which is considerably harder if a non-profit controls a commercial entity,” said Gil Luria, analyst at D.A. Davidson.

OpenAI’s structure drew attention in November 2023 during one of the biggest boardroom dramas in Silicon Valley, where members of the nonprofit board ousted Altman over a breakdown in communication and loss of trust. He was reinstated after five days, following an outpouring of support from employees and investors.
"""


# --- Pydantic Models for Structured Data ---
@flock_type
class Person(BaseModel):
    """A person mentioned in the article."""

    name: str = Field(..., description="Full name of the person")
    role: str = Field(..., description="Role or title of the person")
    organization: Optional[str] = Field(
        None, description="Organization the person is affiliated with"
    )
    quotes: List[str] = Field(
        default_factory=list,
        description="Direct quotes from this person in the article",
    )


@flock_type
class Event(BaseModel):
    """An event described in the article."""

    name: str = Field(..., description="Name or title of the event")
    date: Optional[str] = Field(
        None, description="Date when the event occurred or will occur"
    )
    location: Optional[str] = Field(
        None, description="Location where the event took place or will take place"
    )
    attendees: Optional[int] = Field(
        None, description="Number of attendees if mentioned"
    )
    description: str = Field(..., description="Brief description of the event")


@flock_type
class Product(BaseModel):
    """A product mentioned in the article."""

    name: str = Field(..., description="Name of the product")
    company: str = Field(..., description="Company that makes the product")
    description: str = Field(..., description="Description of the product")
    release_date: Optional[str] = Field(None, description="Release date if mentioned")
    pricing: Optional[str] = Field(None, description="Pricing information if mentioned")
    features: List[str] = Field(
        default_factory=list, description="Key features of the product"
    )


@flock_type
class FinancialData(BaseModel):
    """Financial information mentioned in the article."""

    entity: str = Field(
        ..., description="Company or organization the financial data relates to"
    )
    data_type: str = Field(
        ..., description="Type of financial data (e.g., stock price, investment)"
    )
    value: str = Field(
        ..., description="The financial value with currency or percentage"
    )
    date: Optional[str] = Field(
        None, description="Date associated with the financial data"
    )
    context: str = Field(
        ..., description="Brief context about this financial information"
    )


@flock_type
class ArticleMetadata(BaseModel):
    """Metadata about the article itself."""

    title: str = Field(..., description="Title of the article")
    author: Optional[str] = Field(None, description="Author of the article")
    publication_date: Optional[str] = Field(
        None, description="Original publication date"
    )
    update_date: Optional[str] = Field(
        None, description="Last update date if different from publication"
    )
    category: str = Field(..., description="Category or topic of the article")


@flock_type
class ArticleAnalysis(BaseModel):
    """Complete structured analysis of a news article."""

    metadata: ArticleMetadata = Field(..., description="Metadata about the article")
    people: List[Person] = Field(..., description="People mentioned in the article")
    events: List[Event] = Field(..., description="Events described in the article")
    products: List[Product] = Field(
        ..., description="Products mentioned in the article"
    )
    financial_data: List[FinancialData] = Field(
        default_factory=list, description="Financial information mentioned"
    )
    key_points: List[str] = Field(
        ..., description="Key points or takeaways from the article"
    )
    sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
        ..., description="Overall sentiment of the article"
    )


# --- Flock (Declarative) Approach ---


def run_flock_extraction(article_text: str):
    """Extracts structured data from an article using the Flock declarative approach."""
    # 1. Create Flock Instance
    flock = Flock(name="article_analyzer", model=MODEL, show_flock_banner=False)

    print_subheader("Flock (Declarative) Approach")

    # 2. Define Agent Declaratively
    # Notice how we define WHAT we want (input, output, description)
    # We don't need to explain HOW to extract each piece of data
    # Imagine the following:
    # Instead of defining our complete system by natural language we describe each property of each object
    # This granularity provides a lot of flexibility and allows us to add or change properties without changing the existing system
    article_analyzer = FlockFactory.create_default_agent(
        name="article_analyzer",
        description="Extracts structured information from news articles.",
        input="article_text: str | The full text of the news article to analyze",
        output="analysis: ArticleAnalysis | A complete structured analysis of the article content",
        temperature=0.2,  # Lower temperature for more consistent extraction
        use_cache=False,  # Disable caching for this example
    )
    flock.add_agent(article_analyzer)

    # 3. Run the Flock
    try:
        console.print("Running Flock agent for structured data extraction...")
        start_time = datetime.now()

        result = flock.run(
            start_agent=article_analyzer, input={"article_text": article_text}
        )

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        print_success(f"Extraction completed in {execution_time:.2f} seconds")

        # 4. Display the results in a structured format
        if hasattr(result, "analysis") and isinstance(result.analysis, ArticleAnalysis):
            display_article_analysis(result.analysis, "cyan")
            return result.analysis
        else:
            print_warning("Agent did not return the expected ArticleAnalysis structure")
            return None

    except Exception as e:
        print_warning(f"Flock agent failed: {e}")
        print_warning("Ensure your API key is set and the model is accessible.")
        return None


# --- Traditional Prompting Approach ---


def run_traditional_extraction(article_text: str):
    """Extracts structured data from an article using traditional detailed prompting."""
    print_subheader("Traditional Prompting Approach")

    # 1. Craft the Detailed Prompt
    # Notice how much more explicit instruction is needed compared to the
    # Flock agent's declarative approach
    system_prompt = """You are an expert system for extracting structured information from news articles.
Your task is to analyze the provided article and extract specific data points in a JSON format."""

    user_prompt = f"""
Analyze the following news article and extract structured information according to these detailed instructions:

{article_text}

Please extract the following information in JSON format:

1. Article Metadata:
   - title: The main headline of the article
   - author: The full name of the author if mentioned
   - publication_date: The original publication date in the format mentioned
   - update_date: The last update date if different from publication date
   - category: The main topic category (e.g., Technology, Business, Politics)

2. People Mentioned:
   For each person mentioned in the article, extract:
   - name: Their full name
   - role: Their job title or role
   - organization: The company or organization they're affiliated with
   - quotes: Any direct quotes attributed to them (as a list of strings)

3. Events:
   For each significant event described, extract:
   - name: Name or title of the event
   - date: When the event occurred or will occur
   - location: Where the event took place or will take place
   - attendees: Number of attendees if mentioned
   - description: Brief description of what the event is

4. Products:
   For each product mentioned, extract:
   - name: Name of the product
   - company: Company that makes the product
   - description: Description of what the product is or does
   - release_date: When the product will be released if mentioned
   - pricing: Any pricing information mentioned
   - features: Key features of the product (as a list of strings)

5. Financial Data:
   For each piece of financial information, extract:
   - entity: The company or organization the data relates to
   - data_type: Type of financial data (stock price, investment, etc.)
   - value: The actual value with currency or percentage
   - date: Date associated with the financial data
   - context: Brief context about this financial information

6. Key Points:
   - A list of 3-5 key points or main takeaways from the article

7. Sentiment:
   - The overall sentiment of the article (positive, negative, neutral, or mixed)

Format your response as a valid JSON object with these exact keys. If information for a field is not available in the article, use null for that field or an empty list [] for list fields.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # 2. Call the LLM directly
    try:
        console.print("Running direct LLM call for structured data extraction...")
        start_time = datetime.now()

        response = litellm.completion(
            model=MODEL,
            messages=messages,
            temperature=0.2,  # Match temperature for fairness
            max_tokens=2000,  # Extraction needs more tokens
        )

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        print_success(f"Extraction completed in {execution_time:.2f} seconds")

        # 3. Process and display the results
        import json

        try:
            extraction_result = json.loads(response.choices[0].message.content.strip())
            # Convert to our Pydantic model for consistent display
            analysis = convert_json_to_article_analysis(extraction_result)
            display_article_analysis(analysis, "magenta")
            return analysis
        except json.JSONDecodeError:
            print_warning("Failed to parse JSON response from traditional approach")
            console.print(response.choices[0].message.content.strip())
            return None

    except Exception as e:
        print_warning(f"Traditional prompt failed: {e}")
        print_warning("Ensure your API key is set and the model is accessible.")
        return None


def convert_json_to_article_analysis(json_data):
    """Converts JSON data from traditional approach to ArticleAnalysis model."""
    # This function helps ensure consistent display between both approaches

    # Convert metadata
    metadata = ArticleMetadata(
        title=json_data.get("title", ""),
        author=json_data.get("author"),
        publication_date=json_data.get("publication_date"),
        update_date=json_data.get("update_date"),
        category=json_data.get("category", "Unknown"),
    )

    # Convert people
    people = []
    for person_data in json_data.get("people", []):
        people.append(
            Person(
                name=person_data.get("name", ""),
                role=person_data.get("role", ""),
                organization=person_data.get("organization"),
                quotes=person_data.get("quotes", []),
            )
        )

    # Convert events
    events = []
    for event_data in json_data.get("events", []):
        events.append(
            Event(
                name=event_data.get("name", ""),
                date=event_data.get("date"),
                location=event_data.get("location"),
                attendees=event_data.get("attendees"),
                description=event_data.get("description", ""),
            )
        )

    # Convert products
    products = []
    for product_data in json_data.get("products", []):
        products.append(
            Product(
                name=product_data.get("name", ""),
                company=product_data.get("company", ""),
                description=product_data.get("description", ""),
                release_date=product_data.get("release_date"),
                pricing=product_data.get("pricing"),
                features=product_data.get("features", []),
            )
        )

    # Convert financial data
    financial_data = []
    for finance_data in json_data.get("financial_data", []):
        financial_data.append(
            FinancialData(
                entity=finance_data.get("entity", ""),
                data_type=finance_data.get("data_type", ""),
                value=finance_data.get("value", ""),
                date=finance_data.get("date"),
                context=finance_data.get("context", ""),
            )
        )

    # Create the full analysis
    analysis = ArticleAnalysis(
        metadata=metadata,
        people=people,
        events=events,
        products=products,
        financial_data=financial_data,
        key_points=json_data.get("key_points", []),
        sentiment=json_data.get("sentiment", "neutral"),
    )

    return analysis


def display_article_analysis(analysis, color):
    """Displays the extracted article analysis in a structured format."""
    # Display metadata
    metadata_panel = Panel(
        f"[bold]Title:[/bold] {analysis.metadata.title}\n"
        f"[bold]Author:[/bold] {analysis.metadata.author or 'Not specified'}\n"
        f"[bold]Published:[/bold] {analysis.metadata.publication_date or 'Not specified'}\n"
        f"[bold]Updated:[/bold] {analysis.metadata.update_date or 'Not specified'}\n"
        f"[bold]Category:[/bold] {analysis.metadata.category}",
        title="Article Metadata",
        border_style=color,
    )
    console.print(metadata_panel)

    # Display people
    if analysis.people:
        people_table = Table(title="People Mentioned", border_style=color)
        people_table.add_column("Name", style="bold")
        people_table.add_column("Role")
        people_table.add_column("Organization")
        people_table.add_column("Quotes")

        for person in analysis.people:
            quotes = (
                "\n".join([f"• {quote}" for quote in person.quotes])
                if person.quotes
                else "None"
            )
            people_table.add_row(
                person.name, person.role, person.organization or "Not specified", quotes
            )

        console.print(people_table)

    # Display events
    if analysis.events:
        events_table = Table(title="Events", border_style=color)
        events_table.add_column("Name", style="bold")
        events_table.add_column("Date")
        events_table.add_column("Location")
        events_table.add_column("Attendees")
        events_table.add_column("Description")

        for event in analysis.events:
            events_table.add_row(
                event.name,
                event.date or "Not specified",
                event.location or "Not specified",
                str(event.attendees) if event.attendees else "Not specified",
                event.description,
            )

        console.print(events_table)

    # Display products
    if analysis.products:
        products_table = Table(title="Products", border_style=color)
        products_table.add_column("Name", style="bold")
        products_table.add_column("Company")
        products_table.add_column("Description")
        products_table.add_column("Release Date")
        products_table.add_column("Pricing")
        products_table.add_column("Features")

        for product in analysis.products:
            features = (
                "\n".join([f"• {feature}" for feature in product.features])
                if product.features
                else "None"
            )
            products_table.add_row(
                product.name,
                product.company,
                product.description,
                product.release_date or "Not specified",
                product.pricing or "Not specified",
                features,
            )

        console.print(products_table)

    # Display financial data
    if analysis.financial_data:
        finance_table = Table(title="Financial Data", border_style=color)
        finance_table.add_column("Entity", style="bold")
        finance_table.add_column("Type")
        finance_table.add_column("Value")
        finance_table.add_column("Date")
        finance_table.add_column("Context")

        for finance in analysis.financial_data:
            finance_table.add_row(
                finance.entity,
                finance.data_type,
                finance.value,
                finance.date or "Not specified",
                finance.context,
            )

        console.print(finance_table)

    # Display key points and sentiment
    key_points = "\n".join([f"• {point}" for point in analysis.key_points])
    summary_panel = Panel(
        f"[bold]Key Points:[/bold]\n{key_points}\n\n"
        f"[bold]Overall Sentiment:[/bold] {analysis.sentiment.capitalize()}",
        title="Summary",
        border_style=color,
    )
    console.print(summary_panel)


# --- Main Execution ---


def run_comparison(article_text):
    """Run both approaches and compare them."""
    print_header("News Article Structured Data Extraction Comparison")

    # Run Flock approach
    flock_result = run_flock_extraction(article_text)

    console.print("\n" + "=" * 80 + "\n")  # Separator

    # Run traditional approach
    traditional_result = run_traditional_extraction(article_text)

    # Show comparison summary
    print_header("Comparison Summary")
    console.print("\n[bold]Declarative (Flock) Approach:[/bold]")
    console.print("✓ Defines the desired output structure using Pydantic models")
    console.print("✓ No need to explain HOW to extract each piece of data")
    console.print("✓ Easy to modify by simply updating the Pydantic models")
    console.print("✓ Validation happens automatically through the type system")

    console.print("\n[bold]Traditional Prompting Approach:[/bold]")
    console.print("✗ Requires detailed instructions for each extraction step")
    console.print("✗ Needs to explain both WHAT to extract and HOW to extract it")
    console.print("✗ Modifications require rewriting the entire prompt")
    console.print("✗ No automatic validation; results may vary in structure")

    console.print("\nThe declarative approach is particularly advantageous when:")
    console.print("1. The output structure is complex with many nested fields")
    console.print("2. Requirements change frequently, requiring schema updates")
    console.print("3. Consistency across multiple runs is important")
    console.print("4. You want to focus on WHAT you need rather than HOW to get it")


if __name__ == "__main__":
    run_comparison(SAMPLE_ARTICLE)

# --- YOUR TURN! ---
# 1. Try with a different article:
#    - Find a news article online and replace SAMPLE_ARTICLE with its content
#    - Run the script again and see how both approaches handle different content
#    - Try to use flock's tools to extract data from https://lite.cnn.com/
#    - What does it mean for the complexity of the 'classic' approach?
#
# 2. Modify the extraction requirements:
#    - For the declarative approach, add a new field to one of the Pydantic models
#      (e.g., add "tone: Literal['formal', 'casual']" to ArticleMetadata)
#    - For the traditional approach, add the same requirement to the detailed prompt
#    - Compare how much easier it is to modify the declarative approach
#
# 3. Add a new entity type:
#    - Create a new Pydantic model for something else to extract (e.g., Organizations)
#    - Add it to the ArticleAnalysis model
#    - Update the traditional prompt to extract the same information
#    - Compare the effort required for both approaches
#
# 4. Try extracting from multiple articles:
#    - Create a list of articles and run both approaches on each
#    - See how consistent the results are across different inputs
