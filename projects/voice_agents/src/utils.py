from pathlib import Path
from datetime import datetime

def plot_graph(graph, name: str):
    """
    Plots the graph and saves it to a file.

    Args:
        graph: The graph to plot.
        name: The name of the graph.
    """
    img_bytes = graph.get_graph().draw_mermaid_png()
    # Create directory if it doesn't exist
    output_dir = Path("graph_plot")
    output_dir.mkdir(exist_ok=True)
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"{name}_{timestamp}.png"
    # Write bytes to file
    with open(filename, "wb") as f:
        f.write(img_bytes)
    print(f"Graph saved to {name}")