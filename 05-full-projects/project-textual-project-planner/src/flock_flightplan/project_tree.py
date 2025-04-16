# src/flock_flightplan/project_tree.py
from textual.widgets import Tree
from textual.widgets.tree import TreeNode
# Import the specific event type
from textual.message import Message # Base class for messages
from rich.style import Style

class ProjectTree(Tree):
    """Tree widget for displaying the project structure."""

    def __init__(self, data):
        # Use a more descriptive label or leave it empty if preferred
        super().__init__("Project Structure")
        self.data = data
        self.node_types = {}  # Maps tree nodes IDs to their node_types
        self.node_selected_handler = None  # Callback for node selection
        self.build_tree()

    def build_tree(self):
        """Build the tree structure from the data."""
        self.clear() # Clear existing nodes if rebuilding
        self.root.expand()
        root_node: TreeNode = self.root # type hint

        # Get allowed children of root
        root_allowed = self.data.root_element.allowed_children

        # Create a mapping of node types to their definitions
        node_types = {node.node_type: node for node in self.data.implementation_plan}

        # Recursively build the tree starting from the children of the conceptual root
        for child_type, cardinality in root_allowed.items():
            if child_type in node_types:
                # Add top-level nodes directly to the root
                child_node = root_node.add(f"{node_types[child_type].emoji} {node_types[child_type].display_name}")
                child_node.expand() # Optionally expand top-level nodes
                # Store the node type for this tree node using its ID
                self.node_types[child_node.id] = child_type
                self._add_children(child_node, node_types[child_type], node_types)
            else:
                # Log or handle cases where a node_type is missing in implementation_plan
                self.app.log.warning(f"Node type '{child_type}' defined in root_element but not found in implementation_plan.")
                
        self.root.expand_all()

    # Override the rich_style property to handle potential style issues
    @property
    def rich_style(self) -> Style:
        """Override to ensure we always return a valid Style object."""
        try:
            return super().rich_style
        except AttributeError:
            # Return a default style if there's an issue with the original style
            return Style()

    def _add_children(self, parent_node: TreeNode, node_data, node_types):
        """Recursively add children to a node."""
        allowed_children = node_data.allowed_children
        for child_type, cardinality in allowed_children.items():
            if child_type in node_types:
                # Check if cardinality allows multiple instances
                create_multiple = cardinality in ["many", "multiple", "0..*", "1..*", "*"]
                
                # Number of instances to create (1 by default, 3 if multiple allowed)
                num_instances = 3 if create_multiple else 1
                
                for i in range(num_instances):
                    # Add instance number suffix if multiple
                    suffix = f" #{i+1}" if create_multiple else ""
                    label = f"{node_types[child_type].emoji} {node_types[child_type].display_name}{suffix}"
                    
                    child_node = parent_node.add(label)
                    # Store the node type for this tree node using its ID
                    self.node_types[child_node.id] = child_type
                    # Recurse
                    self._add_children(child_node, node_types[child_type], node_types)
            else:
                 self.app.log.warning(f"Node type '{child_type}' defined in allowed_children for '{node_data.node_type}' but not found in implementation_plan.")


    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        # Ensure the root node is selected by default if desired, or none
        #self.select_node(self.root) # Selects "Project Structure"
        self.root.expand_all()

    # Use the specific event type for clarity and better type checking
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection event."""
        try:
            event.stop() # Prevent the event bubbling further if needed
            node: TreeNode = event.node

            # Check if the selected node is the root node itself or a node we added
            if node is not self.root and node.id in self.node_types:
                node_type = self.node_types[node.id]
                if self.node_selected_handler:
                    # self.app.log(f"Node selected: ID={node.id}, Type={node_type}") # Debugging line
                    self.node_selected_handler(node_type)
        except Exception as e:
            # Catch any errors that might occur during node selection
            self.app.log.error(f"Error handling node selection: {e}")
            # Optionally notify the user
            if hasattr(self.app, 'notify'):
                self.app.notify(f"Error selecting node: {str(e)}", severity="error")