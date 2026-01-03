from dotenv import load_dotenv
from pydantic import SecretStr
import os

from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from graph.prompts.arxiv import arxiv_prompt
from graph.prompts.nanobanana import nanobanana_prompt
from graph.prompts.summarizer import summarizer_prompt
from graph.tools import arxiv_tools
from graph.state import MyState

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
        tools=arxiv_tools,
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
        tools=[parse_pdf],
        system_prompt=summarizer_prompt,
    )

    return summarizer_agent

def create_image_gen_agent():
    """ Creates the vision agent. """    
    # ======= VISION AGENT =======
    nanobanana = get_openrouter_model("google/gemini-3-flash-preview")

    image_gen_agent = create_agent(
        model=nanobanana,
        tools=arxiv_tools,
        system_prompt=nanobanana_prompt,
    )

    return image_gen_agent

def create_image_reviewer_agent():
    """ Creates the vision agent. """    
    # ======= VISION AGENT =======
    image_reviewer = get_openrouter_model("google/gemini-3-flash-preview")

    image_reviewer_agent = create_agent(
        model=image_reviewer,
        tools=arxiv_tools,
        system_prompt=nanobanana_prompt,
    )

    return image_reviewer_agent