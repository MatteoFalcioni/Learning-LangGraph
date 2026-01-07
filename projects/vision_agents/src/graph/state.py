from langchain.agents import AgentState
from operator import add
from typing import Annotated

class MyState(AgentState):
    """
    State for the graph.
    """
    bookmarked_articles: Annotated[list, add] # list of dictionaries, each containing 'title' and 'id' keys
    downloaded_papers_paths: Annotated[list, add] # list of strings, each containing the path to the downloaded paper
    generated_images: Annotated[list, add]  # list of generated images
    review_status: str     # list of review status from image reviewer (uses default str replace)
