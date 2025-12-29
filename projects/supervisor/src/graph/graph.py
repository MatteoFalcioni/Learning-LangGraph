from langgraph.types import Command
from langchain.agents import create_agent, AgentState
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

from tools.handoffs import handoff_to_gmail_agent, handoff_to_calendar_agent, handoff_to_github_agent
from tools.mcp import GitHubMCPTools
from tools.google_tools import gmail_tools, calendar_tools
from prompts.supervisor import supervisor_prompt
from prompts.mail import gmail_prompt
from prompts.calendar import calendar_prompt
from prompts.github import github_prompt

load_dotenv()

def make_graph(
    checkpointer=None,
    plot_graph=False,
):
    """
    Creates the graph.
    """

    # ======= SUPERVISOR =======
    llm = ChatOpenAI(model="gpt-4o")

    supervisor_agent = create_agent(
        model=llm,
        tools=[handoff_to_gmail_agent, handoff_to_calendar_agent, handoff_to_github_agent],
        system_prompt=supervisor_prompt,
    )

    # ======= SUBAGENTS =======
    gmail_agent = create_agent(
        model=llm,
        tools=gmail_tools,
        system_prompt=gmail_prompt,
    )
    calendar_agent = create_agent(
        model=llm,
        tools=calendar_tools,
        system_prompt=calendar_prompt,
    )
    github_agent = create_agent(
        model=llm,
        tools=[GitHubMCPTools().get_tools()],
        system_prompt=github_prompt,
    )

    # ======= NODES =======
    async def gmail_node(state: AgentState)-> Command[Literal["supervisor"]]:  # return to supervisor 
        
        result = await gmail_agent.ainvoke(state)
        last_msg = result['messages'][-1]

        return Command(
            goto="supervisor",
            update={"messages": HumanMessage(content=last_msg.content)},
        )

    async def calendar_node(state: AgentState)-> Command[Literal["supervisor"]]:  # return to supervisor 
    
        result = await calendar_agent.ainvoke(state)
        last_msg = result['messages'][-1]

        return Command(
            goto="supervisor",
            update={"messages": HumanMessage(content=last_msg.content)},
        )
    
    async def github_node(state: AgentState)-> Command[Literal["supervisor"]]:  # return to supervisor 
        
        result = await github_agent.ainvoke(state)
        last_msg = result['messages'][-1]

        return Command(
            goto="supervisor",
            update={"messages": HumanMessage(content=last_msg.content)},
        )

    # ======= GRAPH  BUILDING =======

    builder = StateGraph(AgentState)

    builder.add_node("supervisor", supervisor_agent, destinations=("gmail_agent", "calendar_agent", "github_agent", "__end__"))  
    builder.add_node("gmail_agent", gmail_node)
    builder.add_node("calendar_agent", calendar_node)
    builder.add_node("github_agent", github_node)
    builder.add_edge(START, "supervisor")  # since we have Command(goto=...) everywhere, we do not need other edges.

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


if __name__ == '__main__':

    from langgraph.checkpoint.memory import InMemorySaver

    print("Initializing graph...")

    checkpointer = InMemorySaver()

    graph = make_graph(checkpointer=checkpointer, plot_graph=True)

    print("Graph Initialized...")