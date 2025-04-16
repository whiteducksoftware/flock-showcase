# src/flock_flightplan/app.py
import asyncio
import json
from pathlib import Path
import httpx
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, Static, Markdown, Tree, TabbedContent, TabPane, TextArea, Log, RichLog # Import Tree
from textual.containers import Container, Horizontal
from textual.widget import Widget, Strip
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown as RichMarkdown

from flock_flightplan import collector, model
from flock_flightplan.agents.flocky import generate_flocky_response
from flock_flightplan.agents.planning import generate_planning_structure
from flock_flightplan.cli import utils
from flock_flightplan.utils import cli_init # Import Widget base class
from flock_flightplan.collector import config
from .project_tree import ProjectTree

cli_header = Text(
        """
                                                                                                                         
    _/_/_/_/       _/       _/                     _/          _/                         _/                             
   _/             _/                  _/_/_/      _/_/_/    _/_/_/_/        _/_/_/       _/        _/_/_/      _/_/_/    
  _/_/_/         _/       _/       _/    _/      _/    _/    _/            _/    _/     _/      _/    _/      _/    _/   
 _/             _/       _/       _/    _/      _/    _/    _/            _/    _/     _/      _/    _/      _/    _/    
_/             _/       _/         _/_/_/      _/    _/      _/_/        _/_/_/       _/        _/_/_/      _/    _/     
                                      _/                                _/                                               
                                 _/_/                                  _/                                                

""",
        style="bold green"
    )

cli_subtitle = (Text("plan anything - implement everything - ｐｏｗｅｒｅｄ ｂｙ ＦＬＯＣＫ\n", style="bold white"))

class StyledTextArea(TextArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.highlights = {}  # Store line/column ranges and their styles
        
    def add_highlight(self, start_line, start_col, end_line, end_col, style_class):
        """Add a highlighted region with a specific style class."""
        key = (start_line, start_col, end_line, end_col)
        self.highlights[key] = style_class
        self.refresh()
    
    def render_line(self, y: int) -> Strip:
        """Override to add styling to specific parts of text."""
        strip = super().render_line(y)
        
        # Apply highlights for this line
        for (start_line, start_col, end_line, end_col), style in self.highlights.items():
            if y >= start_line and y <= end_line:
                # Calculate the affected column range for this line
                if y == start_line and y == end_line:
                    # Highlight is contained within this line
                    col_start, col_end = start_col, end_col
                elif y == start_line:
                    # This is the first line of a multi-line highlight
                    col_start, col_end = start_col, len(strip.text)
                elif y == end_line:
                    # This is the last line of a multi-line highlight
                    col_start, col_end = 0, end_col
                else:
                    # This is a middle line of a multi-line highlight
                    col_start, col_end = 0, len(strip.text)
                
                # Apply styling
                if style == "red":
                    strip.stylize(f"red", col_start, col_end)
                elif style == "blue":
                    strip.stylize(f"blue", col_start, col_end)
                # Add more color options as needed
        
        return strip

class ContentView(Container):
    """Content view for displaying templates."""

    def __init__(self):
        super().__init__(id="content-view")
        self.template_map = {}
        self._current_content_widget: Widget | None = None # Track the current widget (Markdown or Static)

    def on_mount(self) -> None:
        """Load templates when the view is mounted."""
        self._load_templates()

    def _load_templates(self):
        """Load templates from templates.json."""
        try:
            # Ensure the path is correct relative to this file (app.py)
            templates_path = Path(__file__).parent.parent.parent / "templates.json"
            self.app.log(f"Attempting to load templates from: {templates_path}") # Debug log path
            if not templates_path.exists():
                 raise FileNotFoundError(f"Templates file not found at {templates_path}")

            with open(templates_path) as f:
                templates = json.load(f)
                # Ensure it's a list of lists/tuples with 2 elements each
                if isinstance(templates, list) and all(isinstance(item, (list, tuple)) and len(item) == 2 for item in templates):
                    self.template_map = {item[0]: item[1] for item in templates}
                    self.app.log(f"Successfully loaded {len(self.template_map)} templates.")
                else:
                    raise ValueError("templates.json is not in the expected format (list of [key, value] pairs).")

        except FileNotFoundError as e:
             self.app.log.error(f"Template loading error: {e}")
             self._display_message(f"Error: templates.json not found.")
        except json.JSONDecodeError as e:
             self.app.log.error(f"Template parsing error: {e}")
             self._display_message(f"Error: Could not parse templates.json. Invalid JSON.")
        except Exception as e:
             # Catch other potential errors (permissions, format issues)
             self.app.log.error(f"Unexpected error loading templates: {e}", exc_info=True)
             self._display_message(f"Error loading templates: {str(e)}")

    def _clear_content(self):
        """Safely remove the currently displayed widget."""
        if self._current_content_widget:
            try:
                self._current_content_widget.remove()
            except Exception as e:
                # Log if removal fails for some reason (shouldn't normally happen)
                self.app.log.warning(f"Could not remove previous content widget: {e}")
            self._current_content_widget = None

    def _display_message(self, message: str):
        """Helper to display a Static message."""
        self._clear_content()
        self._current_content_widget = Static(message)
        self.mount(self._current_content_widget)

    def show_template(self, node_type: str | None):
        """Show template for the given node type, or clear if None."""
        self._clear_content() # Clear previous content first

        if node_type is None:
            # Optionally show a default message when root or unmapped node is clicked
            # self._display_message("Select a node in the tree to see details.")
            return # Or do nothing

        if node_type in self.template_map:
            markdown_content = self.template_map[node_type]
            # Use a dynamic ID maybe? Or just rely on the parent container
            self._current_content_widget = Markdown(markdown_content) # id=f"md-{node_type}"
            self.mount(self._current_content_widget)
            # self.app.log(f"Displayed template for: {node_type}") # Debug log
        else:
            # This case should ideally only happen if template loading failed
            # or if a node_type exists in data.json but not templates.json
            self.app.log.warning(f"No template found for node type: {node_type}")
            self._display_message(f"No template available for {node_type}")


class FlightPlanApp(App):
    """A Textual app for visualizing project structure as a tree."""

    # *** Reverted CSS back to inline definition ***
    CSS = """
    #app-grid {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 3fr;
        height: 1fr;
    }

    #tree-container {
        height: 100%;
        overflow: auto;
        padding: 1;
    }

    #content-container {
        height: 100%;
        overflow: auto;
        padding: 1;
    }
    
    #cli-grid {
        border: solid grey;
        padding: 1;
    }

    #content-view {
        height: auto;
        width: 100%;
    }
    


    #input-container {
        dock: bottom;
        height: auto;
        margin-bottom: 1;  /* Add margin to prevent overlap with footer */
        padding: 1;
    }

    Input {
        width: 1fr;
    }

    Button {
        width: 1;
    }

    /* Ensure footer is docked properly */
    Footer {
        dock: bottom;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh Tree"),
    ]

    def __init__(self):
        super().__init__()
        self._tree_widget: ProjectTree | None = None
        self._data: dict | None = None
        self._content_view: ContentView | None = None # Will be assigned in compose

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)
        
        with TabbedContent(id="views"):
            
            with TabPane("CLI View", id="cli-tab"):
    
                # Main app content
                with Container(id="cli-grid"):
                    with Container(id="cli-container"):
                        yield RichLog(id="cli-output", markup=True, highlight=True, wrap=True, auto_scroll=True)
                        
                        
            with TabPane("Schema", id="schema-tab"):  # Remove visible parameter
    
                # Main app content
                with Container(id="app-grid"):
                    with Container(id="tree-container"):
                        # Tree will be added later after plan generation
                        pass
                    with Container(id="content-container"):
                        # Create the content view here
                        self._content_view = ContentView()
                        yield self._content_view
                        
            with TabPane("Files", id="files-tab"):
    
                # Main app content
                with Container(id="app-grid"):
                    with Container(id="file-tree-container"):
                        # Tree will be added later in on_mount or update_tree
                        yield Tree("Files")
                    with Container(id="file-editor-container"):
                        # Create the content view here
                        yield TextArea()
                        
            

        
        # Input container - add it BEFORE the footer
        with Horizontal(id="input-container"):
            yield Input(placeholder="Enter command or message... /help for help", id="msg-input")
            yield Button(">", id="fetch-button")
        
        # Footer comes last
        yield Footer()
        

    def on_mount(self) -> None:
        """Load the initial data when the app is mounted."""
        # Don't load data on startup anymore
        # self.load_local_data()
        
        # Hide the schema tab on startup
        # tabbed_content = self.query_one("#views", TabbedContent)
        # schema_tab = self.query_one("#schema-tab", TabPane)
        # tabbed_content.remove_pane(schema_tab)
        
        log = self.query_one("#cli-output", RichLog)
        collector.set_app_log(log)
        
        log.write(cli_header,animate=True)
        log.write(cli_subtitle)
        log.write(Text("\n\nFlocky > Hello, I'm Flocky! How can I help you today? Please enter your command or message below.\n", style="bold white"))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle submit event when Enter is pressed in the input field."""
        if event.input.id == "msg-input":
            msg = event.value.strip()
            log = self.query_one("#cli-output", RichLog)
            log.write(Text(f"\n{msg}\n", style="bold green"))
            if msg == "/collect":
                repository = collector.run_collection(
                include_args=['py:.'],
                exclude_args=[],
                calculate_metrics=False,
                )
                # Display repository using rich rendering methods
                repository.render_summary()
                repository.render_files()
                repository.save_to_json("repository.json")
                repository.save_to_markdown("repository.md")
                utils.print_success("Repository object saved to repository.json and repository.md")
                event.input.value = ""
                return
            if msg:
                
                
                # Temporarily disable input to prevent multiple submissions
                event.input.disabled = True
                
                # Run the async fetch task in the background
                self.run_worker(self.fetch_data(msg), exclusive=False, thread=True)
                #self.run_worker(self.fetch_data(msg), exclusive=False)
                
                # Clear the input field
                event.input.value = ""
            else:
                self.notify("Please enter a valid message", severity="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press event."""
        if event.button.id == "fetch-button":
            msg_input = self.query_one("#msg-input", Input)
            msg = msg_input.value.strip()
            log = self.query_one("#cli-output", RichLog)
            log.write(Text(f"\n{msg}\n", style="bold green"))
            if msg == "/collect":
                repository = collector.run_collection(
                include_args=['py:.'],
                exclude_args=[],
                calculate_metrics=False,
                )
                # Display repository using rich rendering methods
                repository.render_summary()
                repository.render_files()
                repository.save_to_json("repository.json")
                repository.save_to_markdown("repository.md")
                utils.print_success("Repository object generated successfully")
                msg_input.value = ""
                return
            
            
            if msg:
                # Temporarily disable input to prevent multiple submissions
                msg_input.disabled = True
                
                # Run the async fetch task in the background
                self.run_worker(self.fetch_data(msg), exclusive=False, thread=True)
                
                # Clear the input field
                msg_input.value = ""
            else:
                self.notify("Please enter a valid message", severity="warning")
                msg_input.focus()

    def load_local_data(self):
        """Load data from local file data.json."""
        data_path = Path(__file__).parent.parent.parent / "data.json"
        self.log(f"Attempting to load data from: {data_path}") # Debug log path
        try:
            if not data_path.exists():
                 raise FileNotFoundError(f"Data file not found at {data_path}")
            with open(data_path) as f:
                self._data = json.load(f)
            self.log("Data loaded successfully. Updating tree.")
            self.update_tree() # Build tree with loaded data
        except FileNotFoundError as e:
             self.notify(f"Error: data.json not found.", severity="error", timeout=10)
             self.log.error(f"Data loading error: {e}")
        except json.JSONDecodeError as e:
             self.notify(f"Error: Could not parse data.json. Invalid JSON.", severity="error", timeout=10)
             self.log.error(f"Data parsing error: {e}")
        except Exception as e:
             self.notify(f"Error loading local data: {str(e)}", severity="error", timeout=10)
             self.log.error(f"Unexpected error loading data: {e}", exc_info=True)


    def update_tree(self):
        """Update or create the tree with the current data."""
        if not self._data:
            self.notify("No data available to build the tree.", severity="warning")
            return

        tree_container = self.query_one("#tree-container")

        # If tree exists, remove it first
        if self._tree_widget:
            try:
                self._tree_widget.remove()
            except Exception as e:
                 self.log.warning(f"Could not remove previous tree widget: {e}")
            self._tree_widget = None

        # Create and mount the new tree
        try:
            self._tree_widget = ProjectTree(self._data)
            # Assign the handler method from *this* app instance
            self._tree_widget.node_selected_handler = self.on_tree_node_selected
            tree_container.mount(self._tree_widget)

            self.log("Project tree updated and mounted.")
            # Optional: Clear content view when tree refreshes
            if self._content_view:
                 self._content_view.show_template(None)

        except Exception as e:
            self.notify("Failed to build project tree.", severity="error")
            self.log.error(f"Error creating/mounting ProjectTree: {e}", exc_info=True)


    def on_tree_node_selected(self, node_type: str | None):
        """Handle tree node selection, called by ProjectTree."""
        if self._content_view:
             # self.log(f"App received node selection: {node_type}") # Debug log
             self._content_view.show_template(node_type)

    async def fetch_data(self, msg):
        """Fetch data from the provided URL."""
        self.notify(f"Processing your request...", timeout=3)
        
        # Enable the input field immediately to allow continued interaction
        msg_input = self.query_one("#msg-input", Input)
        msg_input.disabled = False
        
        # Show loading indicator in the CLI output
        log = self.query_one("#cli-output", RichLog)
        log.write(Text("Flocky > Thinking... 🤔", style="bold blue"))
        
        try:
            # Run API calls in background worker
            result_planning = await asyncio.wait_for(generate_planning_structure(msg), timeout=30)
            
            # Update loading message to show progress
            log.write(Text("Flocky > Planning structure generated, creating detailed response... ⏳", style="bold blue"))
            
            result_flocky = await asyncio.wait_for(generate_flocky_response(msg, result_planning), timeout=30)
            
            def process_results():
                log = self.query_one("#cli-output", RichLog) # Get log ref inside the thread-safe call
                log.write(Text(f"\nFlocky > {result_flocky.answer}\n", style="bold white"))

                # Update app state
                self._data = result_flocky.project_plan
                templates = getattr(result_flocky.project_plan, 'markdown_templates', None) # Safely get templates
                if isinstance(templates, list) and all(isinstance(item, (list, tuple)) and len(item) == 2 for item in templates):
                     if self._content_view: # Ensure content view exists
                         self._content_view.template_map = {item[0]: item[1] for item in templates}
                         self.log(f"Successfully loaded {len(self._content_view.template_map)} templates from response.")
                elif templates is not None: # Log only if templates existed but were wrong format
                    self.log.warning(f"Received templates in unexpected format: {type(templates)}")

                self.notify("Data fetched successfully!", title="Success")
                self.update_tree() # Rebuild tree with new data
            self.call_from_thread(process_results)
            return result_flocky
            
        except httpx.HTTPStatusError as e:
            log = self.query_one("#cli-output", RichLog)
            log.write(Text(f"Flocky > Sorry, I encountered an HTTP error: {e.response.status_code}\n", style="bold red"))
            
            self.notify(f"HTTP Error {e.response.status_code}", severity="error", timeout=10)
            self.log.error(f"HTTP Error: {e}")
            
        except httpx.RequestError as e:
            log = self.query_one("#cli-output", RichLog)
            log.write(Text(f"Flocky > Sorry, I encountered a network error. Please check your connection and try again.\n", style="bold red"))
            
            self.notify(f"Network Error", severity="error", timeout=10)
            self.log.error(f"Request Error: {e}")
            
        except json.JSONDecodeError as e:
            log = self.query_one("#cli-output", RichLog)
            log.write(Text(f"Flocky > Sorry, I received an invalid response format. Please try again.\n", style="bold red"))
            
            self.notify(f"Invalid response format", severity="error", timeout=10)
            self.log.error(f"JSON Decode Error: {e}")
            
        except Exception as e:
            log = self.query_one("#cli-output", RichLog)
            log.write(Text(f"Flocky > Sorry, an unexpected error occurred: {str(e)}\n", style="bold red"))
            
            self.notify(f"Error processing request", severity="error", timeout=10)
            self.log.error(f"Unexpected fetch error: {e}", exc_info=True)


    def action_refresh(self) -> None:
        """Refresh the tree using existing data."""
        if self._data:
            self.log("Refreshing tree view...")
            self.update_tree()
            self.notify("Tree refreshed")
        else:
            self.notify("No data loaded to refresh from. Try loading local data or fetching.", severity="warning")