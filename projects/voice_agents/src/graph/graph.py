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
from graph.prompt import arxiv_prompt
from graph.tools import arxiv_tools
from graph.state import MyState

async def make_graph(
    checkpointer=None,
    plot_graph=False,
):
    """
    Creates the graph.
    """
    load_dotenv()

    # ======= ARXIV agent =======
    if os.getenv('OPENAI_API_KEY'):
        model = "gpt-4.1"
        arxiv_llm = ChatOpenAI(model=model)
    else:
        raise RuntimeError(f"No OpenRouter or OpenAI API keys provided. Provide at least one in your .env file")

    print(f"\n--- Using model : {model} ---")

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
    import sys
    from pathlib import Path
    
    # Add src directory to Python path for absolute imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
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