from langchain.agents import AgentState
from operator import add
from typing import Annotated

class MyState(AgentState):
    """
    State for the graph.
    Bookmarked_articles will be a list of dictionaries, each containing 'title' and 'id' keys. 
    It will store the bookmarked articles' titles and ids.
    """
    bookmarked_articles: Annotated[list, add] # list of dictionaries, each containing 'title' and 'id' keys
    downloaded_papers_paths: Annotated[list, add] # list of strings, each containing the path to the downloaded paper
    generated_images: Annotated[list, add] # list of strings, each containing the URL of the generated image
    review_status: str # list of review status from image reviewer (uses default str replace)
    pdf_base64: str # the base64 encoded PDF
