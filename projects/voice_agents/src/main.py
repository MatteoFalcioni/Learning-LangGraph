import sys
from pathlib import Path

# Add src directory to Python path for absolute imports
sys.path.insert(0, str(Path(__file__).parent))

from STT.flux import flux_stt
from graph.graph import make_graph
import asyncio
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

if __name__ == "__main__":

    async def main():
        print("Initializing graph...")
        checkpointer = InMemorySaver()
        graph = await make_graph(checkpointer=checkpointer)
        print("Graph initialized")

        print("Running voice agent...")

        config = {"configurable" : {"thread_id" : "0", "recursion_limit" : 35}} 

        await flux_stt(graph=graph, config=config)

    asyncio.run(main())