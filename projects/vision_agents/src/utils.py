from datetime import datetime
from pathlib import Path
from langchain_core.messages import HumanMessage
from graph.state import MyState
import base64

def add_imgs(state: MyState) -> HumanMessage:
    """
    Helper to create multimodal message from state

    Args:
        state (MyState): The state of the graph

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

def add_pdfs(state: MyState) -> HumanMessage:
    """
    Helper to add the pdf to the input message

    Args:
        state (MyState): The state of the graph

    Returns:
        message (HumanMessage): The message with the pdf
    """    
    msg = "Summarize the content of this document"
    content_blocks = [{"type": "text", "text": msg}]   # it is a list of typed dicts, see https://docs.langchain.com/oss/python/langchain/messages#multimodal
    
    for pdf_path in state.get("downloaded_papers_paths", []):
        with open(pdf_path, "rb") as f:
            pdf_b64 = base64.b64encode(f.read()).decode("utf-8")
        content_blocks.append({
            "type": "file",
            "base_64": pdf_b64,
            "mime_type": "application/pdf"
        })
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