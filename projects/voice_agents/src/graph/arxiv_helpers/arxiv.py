import arxiv
from typing import Literal
import os
import pymupdf

def search_arxiv(
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
        # e.g., "2103.00020_Attention_Is_All_You_Need.pdf"
        safe_title = "".join(c for c in paper.title if c.isalnum() or c in (' ', '_', '-')).rstrip()
        safe_title = safe_title.replace(" ", "_")
        filename = f"{paper_id}_{safe_title}.pdf"
        
        # Download
        path = paper.download_pdf(dirpath=save_dir, filename=filename)
        return f"Successfully downloaded file to: {path}"
        
    except StopIteration:
        return f"Error: Paper with ID {paper_id} not found."
    except Exception as e:
        return f"Error downloading paper: {str(e)}"


def read_pdf_text(filepath: str):
    """
    Reads the text from a PDF file.
    """
    with open(filepath, 'rb') as file:
        reader = pymupdf.open(file)
        text = ""
        for page in reader:
            text += page.get_text()
        return text