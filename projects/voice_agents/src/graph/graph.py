from dotenv import load_dotenv
from pydantic import SecretStr
import os
from langgraph.graph import StateGraph, START, END
from pathlib import Path
from datetime import datetime
from langchain.messages import HumanMessage
from langchain.agents.middleware import HumanInTheLoopMiddleware

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from prompt import arxiv_prompt
from tools import arxiv_tools
from state import MyState

async def make_graph(
    checkpointer=None,
    plot_graph=False,
):
    """
    Creates the graph.
    """
    load_dotenv()

    # ======= ARXIV =======

    # grok fast if openrouter is available, otherwise gpt-4.1-mini
    if os.getenv['OPENROUTER_API_KEY']:
        # https://openrouter.ai/qwen/qwen3-coder/providers
        arxiv_llm = ChatOpenAI(
            model="qwen/qwen3-coder-flash", 
            
            # redirect LangChain to OpenRouter
            base_url="https://openrouter.ai/api/v1",

            # pass the OpenRouter key
            api_key=SecretStr(os.environ["OPENROUTER_API_KEY"])
        )
    elif os.getenv['OPENROUTER_API_KEY']:
        arxiv_llm = ChatOpenAI(model="gpt-4.1-mini")
    else:
        raise RuntimeError(f"No OpenRouter or OpenAI API keys provided. Provide at least one in your .env file")

    arxiv_agent = create_agent(
        model=arxiv_llm,
        tools=arxiv_tools,
        system_prompt=arxiv_prompt,
        state_schema = MyState,
        middleware = HumanInTheLoopMiddleware(
            interrupt_on = {
                "download_pdf": {
                    "allowed_decisions": [
                        "approve",
                        "reject"
                    ]
                }
            }
        )
    )

    # build the graph 
    graph = StateGraph(MyState)

    graph.add_node("arxiv", arxiv_agent)

    graph.add_edge(START, "arxiv")
    graph.add_edge("arxiv", END)

    graph = graph.compile(checkpointer=checkpointer)

    # plot the graph
    if plot_graph:
        img_bytes = graph.get_graph().draw_mermaid_png()
        # Create directory if it doesn't exist
        output_dir = Path("graph_plot")
        output_dir.mkdir(exist_ok=True)
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_dir / f"arxiv_{timestamp}.png"
        # Write bytes to file
        with open(filename, "wb") as f:
            f.write(img_bytes)
        print(f"Graph saved to {filename}")

    return graph

if __name__ == "__main__":
    import asyncio
    from langgraph.checkpoint.memory import InMemorySaver

    async def main():
        print("Initializing graph...")
        checkpointer = InMemorySaver()
        graph = await make_graph(checkpointer=checkpointer)
        print("Graph initialized")

        # invoke
        msg = """What are the most relevant papers on the topic of AI? 
        Check the five most relevant ones and save the most relevant locally."""

        result = await graph.ainvoke(
                {
                    "messages": [HumanMessage(content=msg)]
                },
                config = {"configurable" : {"thread_id" : "0"}}                
            )
        print(result['messages'][-1].content)

    asyncio.run(main())