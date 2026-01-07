from langchain.agents import AgentState
from operator import add
from typing import Annotated
from typing import Literal

def next_reducer(
    left: Literal["summarizer", "end"] | None,
    right: Literal["summarizer", "end"] | None
) -> Literal["summarizer", "end"]:
    """
    The next reducer function.

    Performs string replace, but initializes left to 'end'
    """
    if left is None:
        return "end"

    return right

class MyState(AgentState):
    """
    State for the graph.
    """
    bookmarked_articles: Annotated[list, add] # list of dictionaries, each containing 'title' and 'id' keys
    downloaded_papers_paths: Annotated[list, add] # list of strings, each containing the path to the downloaded paper
    generated_images: Annotated[list, add]  # list of generated images urls
    review_status: str     # list of review status from image reviewer (uses default str replace)
    pdf_base64: str # the base64 encoded PDF (only last pdf is kept in state)
    summary: str # the summary of the PDF
    next: Annotated[Literal["summarizer", "end"], next_reducer] # the next node to route to