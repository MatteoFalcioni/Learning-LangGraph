from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
import asyncio
from dotenv import load_dotenv
from display_utils import console, rich_print
from rich.panel import Panel

from graph.graph import make_graph

async def main():

    load_dotenv()

    checkpointer = InMemorySaver()

    graph = await make_graph(
        checkpointer=checkpointer
    )

    config = {"thread_id": "1"}
    
    # Pretty header
    console.print("\n", Panel.fit(
        "[bold cyan]🤖 Interactive Supervisor Agent[/bold cyan]",
        border_style="cyan"
    ))
    console.print("[dim]Type 'exit' or 'quit' to end the session[/dim]\n")

    while True:
        # Get user input
        try:
            user_input = console.input("[bold blue]You:[/bold blue] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n\n[dim]Exiting chat...[/dim]")
            break
        
        if not user_input:
            continue
            
        if user_input.lower() in ['exit', 'quit']:
            console.print("\n[dim]Exiting chat...[/dim]")
            break
        
        # Create state with user message
        state = {"messages": [HumanMessage(content=user_input)]}
        
        # Stream agent response
        async for chunk in graph.astream(state, config=config):
            for node_name, values in chunk.items():
                if 'messages' in values:
                    msg = values['messages'][-1] if isinstance(values['messages'], list) else values['messages']
                    rich_print(msg.content, node_name)
        
        # Separator
        console.print("\n" + "─" * 62 + "\n", style="dim")

if __name__ == "__main__":
    asyncio.run(main())