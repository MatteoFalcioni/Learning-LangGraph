from langchain.agents import AgentState
from operator import add
from typing import Annotated

class MyState(AgentState):
    """
    State for the graph.
    Articles will be a list of article id's. It will store the downloaded articles.
    """
    articles: Annotated[list, add] 