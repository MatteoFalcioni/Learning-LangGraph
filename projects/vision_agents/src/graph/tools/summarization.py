from langchain_core.tools import tool
from langgraph.types import Command
from typing import Annotated
from langchain.tools import ToolRuntime
from langchain.messages import ToolMessage
    
@tool
def produce_summary(summary: Annotated[str, "The summary of the paper"], runtime: ToolRuntime) -> Command:
    """
    Produces a summary of a paper.
    """
    return Command(
        update={
            "messages" : [ToolMessage(content=f"Summary produced succesfully and saved to summaries/ folder", tool_call_id=runtime.tool_call_id)],
            "paper_summary" : [summary]
        }
    )