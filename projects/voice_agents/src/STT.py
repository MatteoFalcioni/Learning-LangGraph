import asyncio
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
import os
from dotenv import load_dotenv
import pyaudio
import threading

# Set your key here or in .env
load_dotenv()
API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not API_KEY:
    raise ValueError("DEEPGRAM_API_KEY is not set")

async def main():
    client = AsyncDeepgramClient(api_key=API_KEY)

    # Use listen.v2 for Flux (better for agents)
    async with client.listen.v2.connect(
        model="flux-general-en",
        encoding="linear16",
        sample_rate=16000
    ) as connection:

        def on_message(message, **kwargs):
            # Flux sends transcription results in 'transcript'
            if hasattr(message, 'transcript') and message.transcript:
                print(f"🎤 {message.transcript}")
            
            # This is the VAD trigger for LangGraph
            # Flux v2 automatically detects when the user stops speaking
            if getattr(message, "type", None) == "EndOfTurn":
                print("--- Turn Ended. Invoking LangGraph... ---")
                # result = langgraph_app.invoke({"input": accumulated_text})

        # Register handlers
        connection.on(EventType.MESSAGE, on_message)
        connection.on(EventType.ERROR, lambda error: print(f"Error: {error}"))

        # Start the microphone using pyaudio
        # Audio settings
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        SAMPLE_RATE = 16000
        
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        print("Listening... (Press Ctrl+C to stop)")
        
        # Flag to control streaming
        streaming = True
        
        # Function to read audio and send to Deepgram (runs in thread)
        def stream_audio():
            try:
                while streaming:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    # Use asyncio.run_coroutine_threadsafe to call async send from thread
                    asyncio.run_coroutine_threadsafe(connection.send(data), loop)
            except Exception as e:
                print(f"Streaming error: {e}")
            finally:
                stream.stop_stream()
                stream.close()
                audio.terminate()
        
        # Get the event loop for this coroutine
        loop = asyncio.get_event_loop()
        
        # Start streaming in a separate thread
        stream_thread = threading.Thread(target=stream_audio, daemon=True)
        stream_thread.start()
        
        try:
            # Keep the main coroutine running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            streaming = False
            stream.stop_stream()
            stream.close()
            audio.terminate()
            print("\nStopped listening.")

if __name__ == "__main__":
    asyncio.run(main())