import asyncio
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
import os
from dotenv import load_dotenv
import pyaudio
import threading
from queue import Queue

# ---------------------------------------------------------------
# Example of using Flux for STT : 
# automatically ends the recording when the user stops speaking
# We will use this implementation 
# --------------------------------------------------------------

# Set your key here or in .env
load_dotenv()
API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not API_KEY:
    raise ValueError("DEEPGRAM_API_KEY is not set")

async def stream_graph_task(graph, transcript, config=None, system_message=None):
    """
    Stream the graph execution with the user transcript.
    Will be used in the flux_stt function to stream the graph execution with the user transcript.
    Args:
        graph: The compiled StateGraph to stream.
        transcript: The user transcript to stream.
        config: The config to use for the graph.
        system_message: Optional system message to prepend to each transcript.
    """
    try:
        print(f"\n🤖 Processing: '{transcript}'")
        
        # Build messages list
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": transcript})
        
        async for event in graph.astream(
            {"messages": messages},
            config=config,
            stream_mode="updates"
        ):
            # Print each node's output as it streams
            for node_name, node_output in event.items():
                print(f"[{node_name}]\n\n {node_output}\n\n")
    except Exception as e:
        print(f"❌ [Graph Error] {e}")


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

        def on_flux_message(message, **kwargs):
            nonlocal transcript
            # Handle TurnInfo events (Flux-specific)
            if hasattr(message, 'type') and message.type == 'TurnInfo':
                if hasattr(message, 'event') and message.event == 'EndOfTurn':
                    if hasattr(message, 'transcript') and message.transcript:
                        transcript = message.transcript.strip()
                        print(f"✓ Transcript: '{transcript}'")
                        
                        if graph:
                            # Run graph in async task so it doesn't block audio streaming
                            asyncio.create_task(
                                stream_graph_task(graph, transcript, config, system_message)
                            )

                        transcript = ""
                        
        # Register handlers
        connection.on(EventType.MESSAGE, on_flux_message)
        connection.on(EventType.ERROR, lambda error: print(f"Error: {error}"))
        connection.on(EventType.OPEN, lambda _: ready.set())

        # Start listening as an async task (not a thread!)
        listen_task = asyncio.create_task(connection.start_listening())

        # Wait for connection to be ready
        await ready.wait()
        print("🎤 Listening... (Press Ctrl+C to stop)")
        
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
            print("\n\nStopping...")
            streaming = False
            # Cancel the listening task
            listen_task.cancel()
            # Give thread a moment to finish
            await asyncio.sleep(0.5)
            print("Stopped listening.")

if __name__ == "__main__":
    # close with ctrl+c
    asyncio.run(flux_stt())