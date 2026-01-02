import sys
from pathlib import Path

# Add src directory to Python path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from langgraph.types import Command
import os
from dotenv import load_dotenv
import pyaudio
import threading
from queue import Queue

from utils import parse_for_interrupt, rich_print, console

# ---------------------------------------------------------------
# Example of using Flux for STT : 
# automatically ends the recording when the user stops speaking
# We will use this implementation in our graph
# --------------------------------------------------------------

# Set your key here or in .env
load_dotenv()
API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not API_KEY:
    raise ValueError("DEEPGRAM_API_KEY is not set")

async def stream_graph_task(graph, transcript, config=None, system_message=None, pending_interrupt=None):
    """
    Stream the graph execution with the user transcript.
    Will be used in the flux_stt function to stream the graph execution with the user transcript.
    Args:
        graph: The compiled StateGraph to stream.
        transcript: The user transcript to stream.
        config: The config to use for the graph.
        system_message: Optional system message to prepend to each transcript.
        pending_interrupt: Dict to track if graph is interrupted (shared state).
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
                    try:
                        if isinstance(values, dict) and 'messages' in values:
                            msg = values['messages'][-1]
                            if hasattr(msg, 'content'):
                                rich_print(node_name, msg.content)
                        elif isinstance(values, str):
                            console.print(f"[dim]{node_name}: {values}[/dim]")
                    except Exception as e:
                        console.print(f"[red]Error processing node {node_name}: {e}[/red]")
            
            # Clear the interrupt state after successful resume
            pending_interrupt['is_interrupted'] = False
            pending_interrupt['snapshot'] = None
            console.print(f"[dim]✓ Graph execution completed[/dim]")
            return True
        
        # Normal execution - new conversation turn
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": transcript})
        
        console.print(f"[dim]🔄 Graph is running...[/dim]")
        
        async for event in graph.astream(
            {"messages": messages},
            config=config,
            stream_mode="updates"
        ):
            for node_name, values in event.items():
                try:
                    if isinstance(values, dict) and 'messages' in values:
                        msg = values['messages'][-1]
                        if hasattr(msg, 'content'):
                            rich_print(node_name, msg.content)
                    elif isinstance(values, str):
                        console.print(f"[dim]{node_name}: {values}[/dim]")
                except Exception as e:
                    console.print(f"[red]Error processing node {node_name}: {e}[/red]")
        
        # After streaming completes, check if graph is interrupted
        state_snapshot = graph.get_state(config)
        if state_snapshot.next:  # If there's a next step, it means we're interrupted
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


async def flux_stt(graph=None, config=None, system_message=None):
    """
    Flux STT (by Deepgram) implementation that streams graph execution on each turn.
    Automatically ends the recording when the user stops speaking.
    Args:
        graph: The compiled StateGraph to stream.
        config: The config to use for the graph. Defaults to None.
        system_message: Optional system message to prepend to each transcript. Defaults to None.
    """
    client = AsyncDeepgramClient(api_key=API_KEY)

    # Audio settings - using ~80ms chunks for optimal Flux performance
    # At 16kHz linear16: 80ms = ~2560 bytes. Using 4096 (~128ms) for simplicity
    CHUNK = 4096
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    SAMPLE_RATE = 16000

    # Queue to pass audio from microphone thread to async loop
    audio_queue = Queue()
    streaming = True

    # Function to capture audio from microphone (runs in separate thread)
    def capture_audio():
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        try:
            while streaming:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_queue.put(data)
        except Exception as e:
            print(f"Audio capture error: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

    # Start microphone capture in background thread
    capture_thread = threading.Thread(target=capture_audio, daemon=True)
    capture_thread.start()

    # Use listen.v2 for Flux (better for agents)
    async with client.listen.v2.connect(
        model="flux-general-en",
        encoding="linear16",
        sample_rate=SAMPLE_RATE,
        eot_threshold=0.9, # higher confidence required for end of turn
        eot_timeout_ms=1000 # end of turn after 1 second of silence
    ) as connection:

        # For tracking transcript and turns
        transcript = ""
        ready = asyncio.Event()
        
        # Track interrupted state
        pending_interrupt = {
            'is_interrupted': False,
            'snapshot': None
        }

        def on_flux_message(message, **kwargs):
            nonlocal transcript
            # Handle TurnInfo events (Flux-specific)
            if hasattr(message, 'type') and message.type == 'TurnInfo':
                if hasattr(message, 'event') and message.event == 'EndOfTurn':
                    if hasattr(message, 'transcript') and message.transcript:
                        transcript = message.transcript.strip()
                        console.print(f"[bold green]✓ Transcript:[/bold green] '{transcript}'")
                        
                        if graph:
                            # Run graph in async task so it doesn't block audio streaming
                            asyncio.create_task(
                                stream_graph_task(graph, transcript, config, system_message, pending_interrupt)
                            )

                        transcript = ""
                        
        # Register handlers
        connection.on(EventType.MESSAGE, on_flux_message)
        connection.on(EventType.ERROR, lambda error: console.print(f"[bold red]Error:[/bold red] {error}"))
        connection.on(EventType.OPEN, lambda _: ready.set())

        # Start listening as an async task (not a thread!)
        listen_task = asyncio.create_task(connection.start_listening())

        # Wait for connection to be ready
        await ready.wait()
        console.print("[bold green]🎤 Listening...[/bold green] [dim](Press Ctrl+C to stop)[/dim]")
        
        try:
            # Main loop: read from queue and send to Deepgram
            while True:
                # Check if there's audio data in the queue
                if not audio_queue.empty():
                    audio_data = audio_queue.get()
                    await connection.send_media(audio_data)
                
                # Small delay to avoid busy-waiting
                await asyncio.sleep(0.01)
                
        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]Stopping...[/bold yellow]")
            streaming = False
            # Cancel the listening task
            listen_task.cancel()
            # Give thread a moment to finish
            await asyncio.sleep(0.5)
            console.print("[bold red]Stopped listening.[/bold red]")

if __name__ == "__main__":
    # close with ctrl+c
    asyncio.run(flux_stt())