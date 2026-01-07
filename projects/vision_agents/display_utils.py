from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Color mapping for different nodes
NODE_COLORS = {
    "arxiv": "bold cyan",
    "summarizer": "bold green",
    "image_gen": "bold blue",
    "image_reviewer": "bold yellow",
}

# Initialize rich console
console = Console()

def rich_print(node_name, content):
    """Pretty print content with node-specific styling"""
    # Get color for this node, default to white
    color = NODE_COLORS.get(node_name, "white")
    
    # Format node name (replace underscores, uppercase)
    node_display = Text(node_name.upper().replace("_", " "), style=color)
    
    # Print in a styled panel
    console.print(
        Panel(
            content,
            title=node_display,
            border_style=color,
            title_align="left",
            padding=(1, 2)
        ),
        new_line_start=True
    )