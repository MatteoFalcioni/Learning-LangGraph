from langchain_core.tools import tool
from langgraph.types import Command
from typing import Annotated
import os
from langchain.tools import ToolRuntime
from langchain.messages import ToolMessage

# NOTE: will this error if both agents read at the same time?
# TODO: use mistral OCR 3 to read here, in order to understand images and markdownify everything
# NOTE: instead of making this a tool, make it a node! after arxiv -> parse downloaded paper -> continue
# I mean: the tool will only read the state var created from the node
@tool
def read_downloaded_paper(runtime: ToolRuntime)-> Command:
    """
    Reads pages from a downloaded arXiv paper.
    """
    state = runtime.state
    parsed_content = state['parsed_papers'][-1]  # get the last parsed paper (the only one) content
    
    return Command(
        {"messages" : [ToolMessage(content=parsed_content, tool_call_id=runtime.tool_call_id)]}
    )