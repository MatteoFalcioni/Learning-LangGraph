import sounddevice as sd
import threading

def read_text(text, model, tts_lock: threading.Event = None):
    """
    Function to read out loud a given text with a Kokoro model. 
    
    Args:
        text: The text to speak
        model: The Kokoro TTS model
        tts_lock: Optional threading.Event to coordinate with STT.
                  When cleared, signals that TTS is playing (STT should pause).
                  When set, signals that TTS is done (STT can resume).
    """
    # Signal that TTS is starting (pause STT)
    if tts_lock:
        tts_lock.clear()
    
    try:
        # This generates the audio numbers in RAM
        samples, sample_rate = model.create(
            text, 
            voice="af_sarah", 
            speed=1.0, 
            lang="en-us"
        )
        
        # Play immediately without saving
        sd.play(samples, sample_rate)
        
        # Wait for audio to finish before continuing
        sd.wait()

    finally:
        # Signal that TTS is done (resume STT)
        if tts_lock:
            tts_lock.set() 
