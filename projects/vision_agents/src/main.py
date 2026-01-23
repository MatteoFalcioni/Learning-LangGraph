from graph.graph import make_graph
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from utils import stream_graph, console
import sys

load_dotenv()

if __name__ == "__main__":
    
    def main():
        console.print("[bold green]Initializing graph...[/bold green]")
        checkpointer = InMemorySaver()
        graph = make_graph(checkpointer=checkpointer, plot=True)
        console.print("[bold green]Graph initialized successfully[/bold green]")
        
        console.print("\n[bold cyan]Vision Agent Chat - Type your queries (or 'exit'/'quit' to stop)[/bold cyan]\n")
        
        while True:
            try:
                # Get user input
                user_query = input("\n[You]: ").strip()
                
                # Check for exit commands
                if user_query.lower() in ['exit', 'quit', 'q']:
                    console.print("\n[bold yellow]Goodbye![/bold yellow]")
                    break
                
                # Skip empty queries
                if not user_query:
                    continue
                
                config = {"configurable": {"thread_id": "0", "recursion_limit": 35}}
                
                # Stream the graph with interrupt handling
                result = stream_graph(
                    graph=graph,
                    query=user_query,
                    config=config
                )
                
                if not result:
                    console.print("\n[bold red]✗ Task failed or timed out[/bold red]")
                
            except KeyboardInterrupt:
                console.print("\n\n[bold yellow]Interrupted. Type 'exit' to quit or continue with a new query.[/bold yellow]")
                continue
            except EOFError:
                # Handle Ctrl+D
                console.print("\n[bold yellow]Goodbye![/bold yellow]")
                break
            except Exception as e:
                console.print(f"\n[bold red]✗ Error: {e}[/bold red]")
                console.print("[dim]Continuing...[/dim]")
                continue
    
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Goodbye![/bold yellow]")
        sys.exit(0)

