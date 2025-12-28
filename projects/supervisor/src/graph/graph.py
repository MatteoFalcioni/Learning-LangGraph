from langgraph.types import Command
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START
from langchain.agents.middleware import SummarizationMiddleware, TodoListMiddleware
from langchain_core.messages import HumanMessage

import os
from pydantic import SecretStr
from typing_extensions import Literal
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

from state import MyState

load_dotenv()


def make_graph(
    checkpointer=None,
    plot_graph=False,
):
    """
    Creates the graph.
    """

    # ======= SUPERVISOR =======
    supervisor_llm = ChatOpenAI(model="")

    supervisor_agent = create_agent(
        model=supervisor_llm,
        tools=[assign_to_gmail_agent, assign_to_calendar_agent, assign_to_github_agent],
        system_prompt=supervisor_prompt,
        name="agent_supervisor",
        state_schema=MyState,
    )

    # ======= SUBAGENTS =======
    gmail_agent = create_agent()
    calendar_agent = create_agent()
    github_agent = create_agent()

    # ======= NODES =======
    async def gmail_node():
        return

    async def calendar_node():
        return
    
    async def github_node():
        return

    # ======= GRAPH  BUILDING =======

    builder = StateGraph(MyState)

    builder.add_node(
        "supervisor", supervisor_agent
    )  # , destinations=("data_analyst", "report_writer", "reviewer", END)
    builder.add_node("gmail_agent", gmail_node)
    builder.add_node("calendar_agent", calendar_node)
    builder.add_node("github_agent", github_node)
    builder.add_edge(
        START, "supervisor"
    )  # since we have Command(goto=...) everywhere, we do not need other edges.

    graph = builder.compile(checkpointer=checkpointer)

    if plot_graph:
        img_bytes = graph.get_graph().draw_mermaid_png()
        # Create directory if it doesn't exist
        output_dir = Path("graph_plot")
        output_dir.mkdir(exist_ok=True)
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_dir / f"supervised_{timestamp}.png"
        # Write bytes to file
        with open(filename, "wb") as f:
            f.write(img_bytes)
        print(f"Graph saved to {filename}")

    return graph