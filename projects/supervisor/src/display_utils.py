from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
import asyncio
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from graph.graph import make_graph

# Initialize rich console
console = Console()

# Color mapping for different nodes
NODE_COLORS = {
    "supervisor": "bold cyan",
    "gmail_agent": "bold green",
    "calendar_agent": "bold yellow",
    "github_agent": "bold magenta"
}

def rich_print(content: str, node_name: str):
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
