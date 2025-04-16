# Flock FlightPlan

A Textual-based CLI app for visualizing project structure as a tree.

## Features

- Visualize project structure from a local JSON file
- Fetch project structure from a REST API
- Interactive tree display with expandable nodes

## Installation

```bash
# Using uv
uv pip install -e .
```

## Usage

Run the application:

```bash
flock-flightplan
```

### Local Data

By default, the application loads data from the `data.json` file in the project root.

### Remote Data

1. Enter a REST API endpoint URL in the input field at the bottom
2. Click "Fetch" to retrieve the data and update the tree

### Keyboard Controls

- `q`: Quit the application
- `r`: Refresh the tree
- Arrow keys: Navigate the tree
- Enter/Space: Expand/collapse tree nodes

## Structure

The application visualizes a tree structure defined in JSON format, where each node can have children according to specific rules defined in the data.
