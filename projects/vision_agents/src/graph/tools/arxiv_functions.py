import arxiv
from typing import Literal
import os
import pymupdf
import requests

def search_arxiv_fn(
    query: str, 
    max_results: int = 10, 
    sort_criterion : Literal['relevance', 'last_submitted'] = 'relevance'
)-> str | list[dict]:
    """
    Searches arXiv for the top N articles based on a query.
    Returns a list of dictionaries containing article ID, title, summary, and authors.
    
    Args:
        query (str): The search query (e.g., "AI agents", "quantum computing").
        max_results (int): The maximum number of results to return. Default is 10.
        sort_criterion (Literal['relevance', 'last_submitted']): The criterion to sort the results by. 
            Default is 'relevance': this sorts by relevance to the query.
            'last_submitted' sorts by the date the article was submitted to the arXiv.
    """
    client = arxiv.Client()

    if sort_criterion == 'relevance':
        sort_by = arxiv.SortCriterion.Relevance
    elif sort_criterion == 'last_submitted':
        sort_by = arxiv.SortCriterion.SubmittedDate
    
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=sort_by
    )
    
    results = []
    
    # client.results() is a generator
    for result in client.results(search):
        results.append({
            # entry_id is a URL like 'http://arxiv.org/abs/2310.12345'
            # We split to get just the ID '2310.12345'
            "id": result.entry_id.split('/')[-1],
            "title": result.title,
            "published": result.published.strftime("%Y-%m-%d"),
            "authors": [author.name for author in result.authors],
            "summary": result.summary.replace("\n", " ") # Clean up newlines in abstract
        })
        
    return results

def get_paper_metadata(paper_id : str):
    """
    Gets the metadata of an arXiv paper given its ID.
    Returns a dictionary containing the paper ID, title, summary, and authors.
    
    Args:
        paper_id (str): The arXiv ID (e.g., "2103.00020").
    
    Returns:
        dict: A dictionary containing the paper ID, title, summary, and authors.
    """
    client = arxiv.Client()
    try:
        search = arxiv.Search(id_list=[paper_id])
        paper = next(client.results(search))
        
        return {
            "id": paper.entry_id.split('/')[-1],
            "title": paper.title,
            "summary": paper.summary.replace("\n", " "),
            "authors": [author.name for author in paper.authors]
        }
    
    except StopIteration:
        return f"Error: Paper {paper_id} not found."
    except Exception as e: # Catch network/API errors
        return f"Error fetching paper metadata: {e}"

def download_arxiv_pdf(paper_id: str, save_dir: str = "./downloads"):
    """
    Downloads the PDF of an arXiv paper given its ID.
    
    Args:
        paper_id (str): The arXiv ID (e.g., "2103.00020").
        save_dir (str): The directory to save the PDF in. Defaults to "./downloads".
    
    Returns:
        str: The file path of the downloaded PDF.
    """
    # Ensure directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    client = arxiv.Client()
    
    # We must "search" by ID to get the paper object
    search = arxiv.Search(id_list=[paper_id])
    
    try:
        paper = next(client.results(search))
        
        # Create a safe filename using the ID and a sanitized title
        # e.g., "Attention_Is_All_You_Need.pdf"
        safe_title = "".join(c for c in paper.title if c.isalnum() or c in (' ', '_', '-')).rstrip()
        safe_title = safe_title.replace(" ", "_")
        filename = f"{safe_title}.pdf"
        
        # Download
        path = paper.download_pdf(dirpath=save_dir, filename=filename)
        return path  # Return just the path, not a message
        
    except StopIteration:
        raise ValueError(f"Error: Paper with ID {paper_id} not found.")
    except Exception as e:
        raise ValueError(f"Error downloading paper: {str(e)}")

def read_arxiv_in_memory(paper_id: str, start_page: int = 1, end_page: int = 3):
    """
    Downloads an arXiv paper and returns text from specific pages.
    Use this to read sections without loading the entire document.
    
    Args:
        paper_id (str): The arXiv ID (e.g., "2103.00020").
        start_page (int): The first page to read (1-based index). Default is 1.
        end_page (int): The last page to read (1-based index). Default is 3.
    """
    # 1. Fetch PDF URL
    client = arxiv.Client()
    try:
        paper = next(client.results(arxiv.Search(id_list=[paper_id])))
        pdf_url = paper.pdf_url
    except StopIteration:
        return f"Error: Paper {paper_id} not found."

    # 2. Download to RAM
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        
        # 3. Open PDF stream
        with pymupdf.open(stream=response.content, filetype="pdf") as doc:
            num_pages = len(doc)
            
            # Validate page numbers
            if start_page < 1: start_page = 1
            if end_page > num_pages: end_page = num_pages
            
            # Convert to 0-based index for PyMuPDF
            # We iterate only the requested range
            text_content = []
            for i in range(start_page - 1, end_page):
                page_text = doc[i].get_text()
                text_content.append(f"--- Page {i+1} ---\n{page_text}")
            
            return "\n".join(text_content)

    except Exception as e:
        return f"Error reading paper: {e}"