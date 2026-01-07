from langgraph.graph import StateGraph, START, END
from pathlib import Path
from langchain.messages import HumanMessage

from vision_agents.graph.agents import create_arxiv_agent, create_image_reviewer_agent, create_summarizer_agent
from vision_agents.graph.state import MyState
from vision_agents.graph.prompts.nanobanana_prompt import nanobanana_prompt
from vision_agents.utils import plot_graph, add_imgs, add_pdfs, nanobanana_generate, save_images_and_get_markdown

def make_graph(
    checkpointer=None,
    plot=False,
):
    """
    Creates the graph.

    Args:
        checkpointer: The checkpointer to use for the graph.
        plot: Whether to plot the graph.

    Returns:
        The graph.

    Raises:
        ValueError: If the review status is missing in the state.
        ValueError: If the review status is invalid.
    """
    arxiv_agent = create_arxiv_agent()
    summarizer_agent = create_summarizer_agent()
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
        """ The summarizer node."""

        # add the pdf as input 
        input_state = add_pdfs(state)
        result = summarizer_agent.invoke(input_state)
        structured_output = result["structured_response"]
        summary = structured_output.summary

        return {
                "messages": [HumanMessage(content="Summary generated successfully")],
                "summary": summary
            }
    
    def image_gen_node(state: MyState):
        """ The image generation node. """
        
        # TODO: example_file_path should be configurable or passed via state
        example_file_path = "example.jpeg"  # This should be configured properly
        image_urls = nanobanana_generate(state, nanobanana_prompt, example_file_path)
        msg = "Succesfully generated images from the PDF"

        return {
                "messages": [HumanMessage(content=msg)],
                "generated_images": image_urls
            }
    
    def image_reviewer_node(state: MyState):
        """ The image reviewer node. """
        input_state = add_imgs(state, mime_type="image/jpeg")
        
        result = image_reviewer_agent.invoke(input_state)
        structured_output = result["structured_response"]

        response = structured_output.decision  # "accepted" or "rejected"
        reasoning = structured_output.reasoning

        return {
            "messages": [HumanMessage(content=reasoning)],
            "review_status": response
        }
    
    def routing_function(state: MyState) -> bool:
        """ Checks if the image was approved. """
        status = state.get('review_status', '')
        if not status:
            raise ValueError("Review status is missing in state. This should never happen.")
        if status == "accepted":
            return "reduce"
        elif status == "rejected":
            return "image_gen"
        else:
            raise ValueError("Review status is invalid. This should never happen.")
    
    def reducer_node(state: MyState):
        """ 
        The reducer node. 
        """
        output_path = save_images_and_get_markdown(state)
        print(f"Final report saved to path: {output_path}")

        return state

    # build the graph 
    graph = StateGraph(MyState)

    graph.add_node("arxiv", arxiv_node)
    graph.add_node("summarizer", summarizer_node)
    graph.add_node("image_gen", image_gen_node)
    graph.add_node("image_reviewer", image_reviewer_node)
    graph.add_node("reduce", reducer_node)

    graph.add_edge(START, "arxiv")
    # branch here: 
    graph.add_edge("arxiv", "summarizer")
    graph.add_edge("arxiv", "image_gen")
    graph.add_edge("image_gen", "image_reviewer")
    graph.add_conditional_edges("image_gen", routing_function)
    graph.add_edge("reduce", END)

    graph = graph.compile(checkpointer=checkpointer)

    # plot the graph
    if plot:
        plot_graph(graph)

    return graph

if __name__ == "__main__":
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
