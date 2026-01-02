"""
Graph execution logic for streaming LangGraph outputs.
Handles graph streaming, interrupts, and output formatting.
"""
import sys
from pathlib import Path

# Add src directory to Python path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langgraph.types import Command
from TTS.tts import read_text
from utils import clean_transcript_tts, parse_for_interrupt, rich_print, console, clean_transcript_display, clean_transcript_tts


def handle_stream_output(node_name, values, tts_engine=None):
    """
    Handle output from a graph stream event.
    
    Args:
        node_name: Name of the node producing output
        values: Output values from the node
        tts_engine: Optional TTS engine to speak the output
    
    Returns:
        The message content if available, None otherwise
    """
    try:
        if isinstance(values, dict) and 'messages' in values:
            msg = values['messages'][-1]
            if hasattr(msg, 'content'):
                rich_print(node_name, clean_transcript_display(msg.content))
                
                # If TTS is enabled, speak the content
                if tts_engine:
                    read_text(clean_transcript_tts(msg.content), tts_engine)
                
                return msg.content
        elif isinstance(values, str):
            console.print(f"[dim]{node_name}: {values}[/dim]")
            return values
    except Exception as e:
        console.print(f"[red]Error processing node {node_name}: {e}[/red]")
    
    return None


async def stream_graph_task(graph, transcript, config=None, pending_interrupt=None, tts_engine=None):
    """
    Stream the graph execution with the user transcript.
    
    Args:
        graph: The compiled StateGraph to stream.
        transcript: The user transcript to stream.
        config: The config to use for the graph.
        pending_interrupt: Dict to track if graph is interrupted (shared state).
        tts_engine: Optional TTS engine to speak graph outputs
    
    Returns:
        True if execution completed without interrupt, False if interrupted.
    """
    try:
        console.print(f"\n🤖 Processing: [bold cyan]'{transcript}'[/bold cyan]")
        
        # If we have a pending interrupt, resume with the transcript as decision
        if pending_interrupt and pending_interrupt.get('is_interrupted'):
            console.print(f"⚡ [yellow]Resuming interrupted graph with:[/yellow] '{transcript}'")

            result = parse_for_interrupt(transcript)
            
            # Handle no_match case - don't resume, stay interrupted
            if result['result'] == 'no_match':
                console.print(f"[bold red]❌ Could not understand '{transcript}'. Please say 'yes' or 'no'.[/bold red]")
                return False  # Stay interrupted, don't resume
            
            # Map yes/no to approve/reject
            if result['result'] == 'yes':
                decision = "approve"
            elif result['result'] == 'no':
                decision = "reject"
            else:
                console.print(f"[bold yellow]⚠️  Unexpected result: {result['result']}[/bold yellow]")
                return False
            
            console.print(f"[bold green]✓ Understood: {decision}[/bold green]")
            console.print(f"[dim]🔄 Graph is running...[/dim]")
            
            # Resume the graph with the user's decision
            async for event in graph.astream(
                Command(resume={"decisions": [{"type": decision}]}),
                config=config,
                stream_mode="updates"
            ):
                for node_name, values in event.items():
                    handle_stream_output(node_name, values, tts_engine)
            
            # Clear the interrupt state after successful resume
            pending_interrupt['is_interrupted'] = False
            pending_interrupt['snapshot'] = None
            console.print(f"[dim]✓ Graph execution completed[/dim]")
            return True
        
        # Normal execution - new conversation turn
        messages = [{"role": "user", "content": transcript}]
        
        console.print(f"[dim]🔄 Graph is running...[/dim]")
        
        async for event in graph.astream(
            {"messages": messages},
            config=config,
            stream_mode="updates"
        ):
            for node_name, values in event.items():
                handle_stream_output(node_name, values, tts_engine)
        
        # After streaming completes, check if graph is interrupted
        state_snapshot = graph.get_state(config)
        if state_snapshot.next:  # If there's a next step, it means we're interrupted
            # could check interrupt flag here too but its the same thing
            console.print(f"\n[bold yellow]⚠️  Graph interrupted! Waiting for your approval to download the paper. Approve by saying 'yes', reject by saying 'no'[/bold yellow]")
            console.print(f"[bold cyan]💬 Say 'yes' or 'no' to continue...[/bold cyan]")
            if pending_interrupt:
                pending_interrupt['is_interrupted'] = True
                pending_interrupt['snapshot'] = state_snapshot
            return False
        
        console.print(f"[dim]✓ Graph execution completed. Listening again...[/dim]")
        return True
        
    except Exception as e:
        console.print(f"[bold red]❌ [Graph Error][/bold red] {e}")
        if pending_interrupt:
            pending_interrupt['is_interrupted'] = False
        return False

