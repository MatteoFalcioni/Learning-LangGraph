from pathlib import Path
from datetime import datetime
from rapidfuzz import process, fuzz
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import re

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


def fuzzy_match(input_str: str, target_strings: list[str], threshold: int = 70) -> dict | None: 
    """
    Performs fuzzy matching to find the best match for the input string
    Args:
        input_str: The input string to match.
        target_strings: The list of target strings to match against (will be either 'yes' or 'no')
        threshold: The threshold for the fuzzy match.
    Returns:
        The best match and the score (if the score is greater than the threshold).
        
        Example: input "Ye .. i accept" returns {"match": "yes", "score": 92}
    """
    # Normalize to lowercase for case-insensitive matching
    input_normalized = input_str.lower().strip()

    match_result = process.extractOne(
        input_normalized,
        target_strings,
        scorer=fuzz.ratio
    )

    if match_result is None:
        return None

    match, score, _ = match_result
    
    if score < threshold:  
        return None
    
    return {'match': match, 'score': score}

def parse_for_interrupt(transcript):
    """
    Function that matches the transcript for interrupt as either approve or reject given a string. 
    Use fuzzy match to match closest string with threshold.
    Args:
        transcript: The transcript to parse.
    Returns:
        {'result' : 'yes' | 'no' | 'no_match'}
    Example:
        input "Yes .. I accept" returns {'result' : 'yes'}
        input "No .. I reject" returns {'result' : 'no'}
        input "I don't know" returns {'result' : 'no_match'}
    """
    target_strings = ["yes", "no"]
    
    result = fuzzy_match(transcript, target_strings)

    if result is None:
        return {'result' : 'no_match'}
    else: 
        match = result['match']
        return {'result' : match}

# Color mapping for different nodes
NODE_COLORS = {
    "arxiv": "bold cyan",
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

def clean_transcript_tts(text):
    """
    Strips transcript text of all text contained inside the dividers <info> </info>,
    and replaces 'arxiv' (case insensitive) with 'archive'
    """
    text = re.sub(r'<info>(.*?)</info>', '', text, flags=re.DOTALL)  # need dotall to match newlines
    text = re.sub(r'arxiv', 'archive', text, flags=re.IGNORECASE) # take out arxiv and use archive for reading
    return text

def clean_transcript_display(text):
    """
    Strips transcript text of only the separator text <info> </info>
    """
    return text.replace('<info>', '').replace('</info>', '')
