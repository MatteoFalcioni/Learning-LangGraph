from graph.graph import make_graph
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from utils import stream_graph_with_interrupt

load_dotenv()

if __name__ == "__main__":
    
    def main():
        print(">>Initializing graph...")
        checkpointer = InMemorySaver()
        graph = make_graph(checkpointer=checkpointer, plot=False)
        print(">>Graph initialized successfully")
        
        print(">>Running vision agent...\n")
        
        config = {"configurable": {"thread_id": "0", "recursion_limit": 35}}
        
        # Example query - you can modify this
        msg = """What are the most relevant papers on the topic of AI agents? 
        Check the five most relevant ones and save the most relevant locally."""
        
        try:
            print(f">>Query: {msg}\n")
            
            # Stream the graph with interrupt handling
            result = stream_graph_with_interrupt(
                graph=graph,
                query=msg,
                config=config,
                timeout_seconds=120
            )
            
            if result:
                print("\n>>Task completed successfully!")
            else:
                print("\n>>Task failed or timed out")
            
        except (KeyboardInterrupt, SystemExit):
            print("\n>>Vision agent stopped by user")
    
    try:
        main()
    except KeyboardInterrupt:
        pass  # Suppress the traceback

