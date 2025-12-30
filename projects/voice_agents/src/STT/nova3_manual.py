import threading
from deepgram import DeepgramClient
from deepgram.core.events import EventType
import os
from dotenv import load_dotenv
import pyaudio

# ------------------------------------------------------------
# Example ending the recording manually from the command line
# ------------------------------------------------------------

# Set your key here or in .env
load_dotenv()
API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not API_KEY:
    raise ValueError("DEEPGRAM_API_KEY is not set")

def main():
    client = DeepgramClient(api_key=API_KEY)

    # Audio settings
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    SAMPLE_RATE = 16000

    # Use listen.v1 for Nova-3 (synchronous client)
    with client.listen.v1.connect(
        model="nova-3",
        language="en",
        encoding="linear16",
        sample_rate=SAMPLE_RATE,
        channels=CHANNELS,
    ) as connection:

        ready = threading.Event()

        def on_message(result):
            event_type = getattr(result, "type", None)
            channel = getattr(result, "channel", None)
            if channel and hasattr(channel, "alternatives"):
                transcript = channel.alternatives[0].transcript
                is_final = getattr(result, "is_final", True)
                if transcript:
                    print(transcript)

        # Register handlers
        connection.on(EventType.OPEN, lambda _: ready.set())
        connection.on(EventType.MESSAGE, on_message)
        connection.on(EventType.ERROR, lambda error: print(f"Error: {error}"))

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

        def stream_audio():
            ready.wait()
            try:
                while True:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    # send_media is synchronous - no await needed!
                    connection.send_media(data)
            except Exception as e:
                print(f"Streaming error: {e}")
            finally:
                stream.stop_stream()
                stream.close()
                audio.terminate()
        
        # Start streaming in a separate thread
        stream_thread = threading.Thread(target=stream_audio, daemon=True)
        stream_thread.start()
        
        print("Listening... (Press Ctrl+C to stop)")
        
        try:
            # start_listening is synchronous - no await needed!
            connection.start_listening()
        except KeyboardInterrupt:
            print("\nStopping...")
            stream.stop_stream()
            stream.close()
            audio.terminate()
            print("Stopped listening.")

if __name__ == "__main__":
    main()