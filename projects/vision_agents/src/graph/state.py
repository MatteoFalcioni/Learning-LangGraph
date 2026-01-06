from langchain.agents import AgentState
from operator import add
from typing import Annotated

class MyState(AgentState):
    """
    State for the graph.
    """
    bookmarked_articles: Annotated[list, add] 
    parsed_papers: Annotated[list, add]  # do not parse twice: not a tool, but a node
