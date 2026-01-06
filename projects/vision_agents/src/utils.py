from datetime import datetime
from pathlib import Path
from langchain_core.messages import HumanMessage
from graph.state import MyState

def prepare_multimodal_message(state: MyState) -> HumanMessage:
    """
    Helper to create multimodal message from state

    Returns:
        message (HumanMessage): The multimodal message
    """    
    msg = "Here are the images to review"
    
    content_blocks = [{"type": "text", "text": msg}]   # it is a list of typed dicts, see https://docs.langchain.com/oss/python/langchain/messages#multimodal
    
    # Add images
    for img_b64 in state.get("generated_images", []):
        content_blocks.append({
            "type": "image",
            "base64": img_b64,
            "mime_type": "image/jpeg"  # TODO: check mime type of generated images by gemini
        })

    # construct the messages as HumanMessage(content_blocks=...)
    message = HumanMessage(content_blocks=content_blocks)  # v1 format, see https://docs.langchain.com/oss/python/langchain/messages#multimodal
    
    return message   # NOTE: returns msg as is, then you need to wrap it in a list!

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