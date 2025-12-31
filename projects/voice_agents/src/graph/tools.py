from arxiv_helpers.arxiv import search_arxiv, download_arxiv_pdf, read_pdf_text
from langchain_core.tools import tool
from langgraph.types import Command
from typing import Annotated
import os

@tool
def search_arxiv(query: Annotated[str, "The query to search in arXiv with"]):
    """
    Search arXiv for papers.
    """
    return search_arxiv(query)

@tool
def download_arxiv_pdf(paper_id: Annotated[str, "The ID of the paper to download from the arXiv"]) -> Command:
    """
    Download the PDF of a paper from the arXiv.
    """
    # here we use Command because we need to act on state with an update
    # (1) download
    download_arxiv_pdf(paper_id)
    # (2) add id to list in state 
    return

@tool
def list_downloads():
    """
    Lists the downloaded articles.
    """
    return os.listdir("./downloads")

@tool
def read_pdf_text(filepath: Annotated[str, "The path to the PDF file to read"]):
    """
    Read the text from a PDF file.
    """
    return read_pdf_text(filepath)