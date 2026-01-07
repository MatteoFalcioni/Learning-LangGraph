from datetime import datetime
from pathlib import Path
import os
import base64
from typing import Literal
from openai import OpenAI
import requests
from langchain_core.messages import HumanMessage
from vision_agents.graph.state import MyState

def add_imgs(state: MyState, mime_type: Literal["image/jpeg", "image/png"]) -> HumanMessage:
    """
    Helper to create multimodal message from state

    Args:
        state (MyState): The state of the graph
        mime_type (Literal["image/jpeg", "image/png"]): The mime type of the images
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
            "mime_type": mime_type
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

def nanobanana_generate(state: MyState, nanobanana_prompt: str, example_file_path: str) -> list[str]:
    """
    Generates an image from a PDF using the Nanobanana model.

    Args:
        state (MyState): The state of the graph
        nanobanana_prompt (str): The prompt for the Nanobanana model
        example_file_path (str): The path to the example image file
    Returns:
        image_urls (list[str]): The list of image URLs

    Raises:
        RuntimeError: If the image generation fails
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )
    with open(example_file_path, "rb") as f:
        example_img = base64.b64encode(f.read()).decode("utf-8")
    response = client.chat.completions.create(
        model="google/gemini-3-pro-image-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": nanobanana_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:application/pdf;base64,{state.get('pdf_base64')}"
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{example_img}"
                        }
                    }
                ]
            }
        ],
        extra_body={"modalities": ["image", "text"]}
    )

    image_urls = []
    response = response.choices[0].message
    if response.images:
        for image in response.images:
            image_url = image['image_url']['url']  # Base64 data URL
            image_urls.append(image_url)
    else:
        raise RuntimeError("Failed to generate image")

    return image_urls

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

def save_images_and_get_markdown(state):
    """
    Saves the images and returns the markdown content.

    Args:
        state (MyState): The state of the graph

    Returns:
        output_path (str): The path to the markdown file
    """
    # Get the summary and the image URLs from the state
    summary = state.get('summary', '')
    image_urls = state.get('generated_images', [])
    
    # Create a directory for images
    os.makedirs("assets", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    markdown_lines = [f"# Summary\n{summary}\n"]

    paths = []
    
    for i, url in enumerate(image_urls):
        image_name = f"summary_image_{i}.png"
        path = os.path.join("assets", image_name)
        paths.append(path)
        
        # Download the actual image data
        img_data = requests.get(url).content
        with open(path, 'wb') as handler:
            handler.write(img_data)        

    # Add local path to markdown but only of first image (only encode one image in the markdown)
    markdown_lines.append(f"![Generated Image]({paths[0]})")
    
    markdown_content = "\n".join(markdown_lines)
    
    # Save the markdown file
    output_path = "reports/report.md" 
    with open(output_path, "w") as f:
        f.write(markdown_content)
    
    return output_path