from dotenv import load_dotenv
from pydantic import SecretStr, BaseModel, Field
import os
from typing import Literal

from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from vision_agents.graph.prompts.arxiv_prompt import arxiv_prompt
from vision_agents.graph.prompts.summarizer import summarizer_prompt
from vision_agents.graph.prompts.image_reviewer import reviewer_prompt
from vision_agents.graph.tools.arxiv_tools import search_arxiv, mark_as_relevant, download_pdf, list_downloads, read_by_page, list_marked_articles
from vision_agents.graph.state import MyState

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

class ArxivResponseSchema(BaseModel):
    """
    Schema for the structured output of the arxiv agent.
    Access it as result["structured_response"]
    """
    message : str = Field(description="The message to the user")
    next: Literal["summarizer", "end"] = Field(description="The next node to route to")

def create_arxiv_agent():
    """ Creates the arxiv agent. """    
    arxiv_llm = ChatOpenAI(model="gpt-4.1")

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
        )],
        response_format=ArxivResponseSchema
    )

    return arxiv_agent

class SummarizerResponseSchema(BaseModel):
        """
        Schema for the summarizer agent response.   
        Access it as result["structured_response"]
        """
        summary: str = Field(description="The summary of the PDF")

def create_summarizer_agent():
    """ Creates the summarizer agent. """    
    summarizer_llm = get_openrouter_model("google/gemini-3-flash-preview")

    summarizer_agent = create_agent(
        model=summarizer_llm,
        system_prompt=summarizer_prompt,
        state_schema=MyState,
        response_format=SummarizerResponseSchema
    )

    return summarizer_agent

class ReviewerResponseSchema(BaseModel):
        """
        Schema for the image reviewer agent response.
        Access it as result["structured_response"]
        """
        decision: Literal["accepted", "rejected"] = Field(description="The decision to accept or reject the image")
        reasoning: str = Field(description="The reasoning for the decision")

def create_image_reviewer_agent():
    """ Creates the reviewer agent: it is a structured output agent"""    
    image_reviewer = get_openrouter_model("google/gemini-2.5-flash")

    image_reviewer_agent = create_agent(
        model=image_reviewer,
        system_prompt=reviewer_prompt,
        state_schema=MyState,
        response_format=ReviewerResponseSchema
    )

    return image_reviewer_agent