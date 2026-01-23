import sys
from pathlib import Path
from typing import Optional

# Add src directory to Python path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
import os
from dotenv import load_dotenv
import pyaudio
import threading
from queue import Queue

from utils import console
from graph.executor import stream_graph_task

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

async def flux_stt(graph=None, config=None, tts_engine=None):
    """
    Flux STT (by Deepgram) implementation that streams graph execution on each turn.
    Automatically ends the recording when the user stops speaking.
    Args:
        graph: The compiled StateGraph to stream.
        config: The config to use for the graph. Defaults to None.
        tts_engine: Optional TTS engine to speak graph outputs. Defaults to None.
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
    
    # TTS lock: when set, STT is active (can send audio to Deepgram)
    # when cleared, TTS is playing (should NOT send audio to Deepgram)
    tts_lock = threading.Event()
    tts_lock.set()  # Initially set = STT is active, TTS is not playing

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
                            # (!) stream_graph_task reads out the output with the TTS model
                            asyncio.create_task(
                                stream_graph_task(graph, transcript, config, pending_interrupt, tts_engine, tts_lock)
                            )

                        transcript = ""
                        
        # Register handlers
        connection.on(EventType.MESSAGE, on_flux_message) # this is saying: whenever you get a message from the server, call this function
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
                    
                    # Check if TTS is currently playing (lock is cleared)
                    is_stt_active = tts_lock.is_set()
                    
                    if is_stt_active:
                        # Normal operation: send audio to Deepgram
                        await connection.send_media(audio_data)
                    else:
                        # TTS is playing: discard the audio to prevent feedback loop
                        # This effectively "drains" the queue while the agent is speaking
                        pass
                
                # Small delay to avoid busy-waiting
                await asyncio.sleep(0.01)
                
        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]Stopping...[/bold yellow]")
            streaming = False
            # Cancel the listening task
            listen_task.cancel()
            try:
                await listen_task
            except asyncio.CancelledError:
                pass
            # Give thread a moment to finish
            await asyncio.sleep(0.5)
            console.print("[bold red]Stopped listening.[/bold red]")
            # Suppress the KeyboardInterrupt after cleanup
            raise SystemExit(0)

if __name__ == "__main__":
    # close with ctrl+c
    asyncio.run(flux_stt())