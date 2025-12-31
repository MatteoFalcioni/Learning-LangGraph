from langchain.agents import AgentState
from operator import add
from typing import Annotated

class MyState(AgentState):
    """
    State for the graph.
    bookmarked_articles will be a list of article id's. It will store the bookmarked articles.
    """
    bookmarked_articles: Annotated[list, add] 