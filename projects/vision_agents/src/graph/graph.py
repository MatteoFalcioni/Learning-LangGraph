from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from pathlib import Path
from langchain.messages import HumanMessage

from graph.agents import create_image_gen_agent, create_arxiv_agent, create_image_reviewer_agent, create_summarizer_agent
from graph.state import MyState
from utils import plot_graph


def make_graph(
    checkpointer=None,
    plot=False,
):
    """
    Creates the graph.
    """
    arxiv_agent = create_arxiv_agent()
    summarizer_agent = create_summarizer_agent()
    image_gen_agent = create_image_gen_agent()
    image_reviewer_agent = create_image_reviewer_agent()

    def arxiv_node(state: MyState):
        """ The arxiv node. """
        result = arxiv_agent.invoke(state)
        last_msg_content = result['messages'][-1].content

        return {
            "messages": [HumanMessage(content=last_msg_content)], 
            "bookmarked_articles": result.get("bookmarked_articles", [])
        }
    
    def summarizer_node(state: MyState):
        """ The summarizer node. """
        result = summarizer_agent.invoke(state)
        last_msg_content = result['messages'][-1].content

        return {
                "messages": [HumanMessage(content=last_msg_content)],
            }
        
    
    def image_gen_node(state: MyState):
        """ The image generation node. """
        result = image_gen_agent.invoke(state)
        last_msg_content = result['messages'][-1].content

        return {
                "messages": [HumanMessage(content=last_msg_content)],
            }
        
    
    def image_reviewer_node(state: MyState):
        """ The image reviewer node. """
        result = image_reviewer_agent.invoke(state)
        last_msg_content = result['messages'][-1].content

        return {
            "messages": [HumanMessage(content=last_msg_content)],
        }

    # build the graph 
    graph = StateGraph(MyState)

    graph.add_node("arxiv", arxiv_node)
    graph.add_node("summarizer", summarizer_node)
    graph.add_node("image_gen", image_gen_node)
    graph.add_node("image_reviewer", image_reviewer_node)

    graph.add_edge(START, "arxiv")
    graph.add_edge("arxiv", END)

    graph = graph.compile(checkpointer=checkpointer)

    # plot the graph
    if plot:
        plot_graph(graph)

    return graph

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add src directory to Python path for absolute imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from langgraph.checkpoint.memory import InMemorySaver


    print("Initializing graph...")
    checkpointer = InMemorySaver()
    graph = make_graph(checkpointer=checkpointer)
    print("Graph initialized")

    # invoke
    msg = """What are the most relevant papers on the topic of AI? 
    Check the five most relevant ones and save the most relevant locally."""

    result = graph.invoke(
            {
                "messages": [HumanMessage(content=msg)]
            },
            config = {"configurable" : {"thread_id" : "0"}}                
        )
    print(result['messages'][-1].content)
