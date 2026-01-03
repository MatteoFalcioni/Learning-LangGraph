from datetime import datetime
from pathlib import Path

def plot_graph(graph):
    """
    Saves the graph to a file.

    The file is saved in the "graph_plot" directory with a timestamped filename.
    The filename is in the format "arxiv_<timestamp>.png".

    Args:
        graph (StateGraph): The graph to plot.
    """
    img_bytes = graph.get_graph().draw_mermaid_png()
    output_dir = Path("graph_plot")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"arxiv_{timestamp}.png"
    with open(filename, "wb") as f:
        f.write(img_bytes)
    print(f"Graph saved to {filename}")