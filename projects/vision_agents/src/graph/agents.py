from dotenv import load_dotenv
from pydantic import SecretStr, BaseModel, Field
import os
from typing import Literal

from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from prompts.arxiv_prompt import arxiv_prompt
from prompts.nanobanana_prompt import nanobanana_prompt
from prompts.summarizer import summarizer_prompt
from prompts.image_reviewer import reviewer_prompt
from tools.arxiv_tools import search_arxiv, mark_as_relevant, download_pdf, list_downloads, read_by_page, list_marked_articles
from tools.shared import read_downloaded_paper
from tools.summarization import produce_summary
from state import MyState

load_dotenv()

def get_openrouter_model(model_name: str):
    """ Returns a ChatOpenAI instance for the given model name using OpenRouter. """ 
    load_dotenv()

    if os.getenv('OPENROUTER_API_KEY'):
        return ChatOpenAI(
            model=model_name, 
            
            # redirect LangChain to OpenRouter
            base_url="https://openrouter.ai/api/v1",

            # pass the OpenRouter key
            api_key=SecretStr(os.environ["OPENROUTER_API_KEY"])
        )
    else:
        raise RuntimeError(f"No OpenRouter API key provided. Provide one in your .env file")

def create_arxiv_agent():
    """ Creates the arxiv agent. """    
    # ======= ARXIV =======
    arxiv_llm = get_openrouter_model("google/gemini-3-flash-preview")

    arxiv_agent = create_agent(
        model=arxiv_llm,
        tools=[search_arxiv, mark_as_relevant, download_pdf, list_downloads, read_by_page, list_marked_articles],
        system_prompt=arxiv_prompt,
        state_schema = MyState,
        middleware = [HumanInTheLoopMiddleware(
            interrupt_on = {
                "download_pdf": {
                    "allowed_decisions": [
                        "approve",
                        "reject"
                    ]
                }
            }
        )]
    )

    return arxiv_agent

def create_summarizer_agent():
    """ Creates the summarizer agent. """    
    # ======= SUMMARIZER AGENT =======
    summarizer_llm = get_openrouter_model("google/gemini-3-flash-preview")

    summarizer_agent = create_agent(
        model=summarizer_llm,
        tools=[produce_summary],
        system_prompt=summarizer_prompt,
        state_schema=MyState
    )

    return summarizer_agent

class ResponseSchema(BaseModel):
        """
        Schema for the image reviewer agent response.
        Access it as result["structured_response"]
        """
        decision: Literal["accepted", "rejected"] = Field(description="The decision to accept or reject the image")
        reasoning: str = Field(description="The reasoning for the decision")

def create_image_reviewer_agent():
    """ Creates the reviewer agent: it is a structured output agent"""    
    # ======= VISION AGENT =======
    image_reviewer = get_openrouter_model("google/gemini-3-flash-preview")

    image_reviewer_agent = create_agent(
        model=image_reviewer,
        system_prompt=reviewer_prompt,
        state_schema=MyState,
        response_format=ResponseSchema
    )

    return image_reviewer_agent