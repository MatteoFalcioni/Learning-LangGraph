from pathlib import Path
from datetime import datetime
from rapidfuzz import process, fuzz

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
    match_result = process.extractOne(
        input_str,
        target_strings,
        scorer=fuzz.token_sort_ratio   
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


    