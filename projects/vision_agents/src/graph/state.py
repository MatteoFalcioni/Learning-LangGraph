from langchain.agents import AgentState
from operator import add
from typing import Annotated

class MyState(AgentState):
    """
    State for the graph.
    """
    bookmarked_articles: Annotated[list, add] 
    parsed_papers: Annotated[list, add]     # list of paper parsed by mistral
    generated_images: Annotated[list, add]  # list of generated images
    review_status: str     # list of review status from image reviewer (uses default str replace)
