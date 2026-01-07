from vision_agents.graph.tools.arxiv_functions import search_arxiv_fn, download_arxiv_pdf, read_arxiv_in_memory, get_paper_metadata
from langchain_core.tools import tool
from langgraph.types import Command
from typing import Annotated
import os
from langchain.tools import ToolRuntime
from langchain.messages import ToolMessage
import base64

@tool
def search_arxiv(query: Annotated[str, "The query to search in arXiv with"], max_results: Annotated[int, "The maximum number of results to return"] = 10):
    """
    Search arXiv for papers.
    """
    print(f"Searching arXiv for papers...")
    return search_arxiv_fn(query, max_results)

@tool
def mark_as_relevant(
    paper_id: Annotated[str, "The ID of the paper to mark as relevant"],
    runtime: ToolRuntime
) -> Command:
    """
    Mark a paper as relevant.
    """
    # here we use command because we add the paper to state 
    metadata = get_paper_metadata(paper_id)
    # if metadata is a dict it worked, otherwise it's an error message
    if isinstance(metadata, dict):
        # add the paper to the list of bookmarked articles
        print(f"Marked paper {metadata['title']} (id: {paper_id}) as relevant")
        return Command(
            update={
                    "messages" : [ToolMessage(content=f"Succesfully marked paper {metadata['title']} (id: {paper_id}) as relevant", tool_call_id=runtime.tool_call_id)],
                    "bookmarked_articles" : [{'title': metadata['title'], 'id': paper_id}]
                }
        )
    else:
        return Command(
            update={
                "messages" : [ToolMessage(content=metadata, tool_call_id=runtime.tool_call_id)],
            }
        )

@tool
def download_pdf(
    runtime: ToolRuntime,
    paper_id: Annotated[str, "The ID of the paper to download from the arXiv"]
) -> Command:
    """
    Download the PDF of a paper from arXiv, given its ID.
    """
    print(f"Attempting to download paper with id: {paper_id}...")

    filepath = download_arxiv_pdf(paper_id)
    with open(filepath, "rb") as f:
        pdf_base64 = base64.b64encode(f.read()).decode("utf-8")
    return Command(
        update={
            "messages" : [ToolMessage(content=f"Successfully downloaded file to: {filepath}", tool_call_id=runtime.tool_call_id)],
            "downloaded_papers_paths": [filepath],
            "pdf_base64": pdf_base64    # NOTE: only the last pdf is kept in the state (encoded)
        }
    )

@tool
def list_marked_articles(runtime: ToolRuntime) -> Command:
    """
    Lists the marked articles.
    """
    return Command(
        update={
            "messages" : [ToolMessage(content=f"The marked articles are: {runtime.state.get('bookmarked_articles', [])}", tool_call_id=runtime.tool_call_id)]
        }
    )

@tool
def list_downloads():
    """
    Lists the downloaded articles.
    """
    return os.listdir("./downloads")

@tool
def read_by_page(
    paper_id: Annotated[str, "The ID of the paper to read from arXiv"], 
    start_page: Annotated[int, "The starting page to read"], 
    end_page: Annotated[int, "The ending page to read"]
):
    """
    Read the text from a paper from the arXiv, given its ID.
    """
    print(f"Reading papers...")
    return read_arxiv_in_memory(paper_id, start_page, end_page)