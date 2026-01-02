import soundfile as sf
import sounddevice as sd
from kokoro_onnx import Kokoro
import time
import os

# Initialize with the .bin file
# espeak_config is optional but good for ensuring fallback on weird words
kokoro = Kokoro("../models/kokoro-v0_19.fp16.onnx", "../models/voices-v1.0.bin")

text = "This is a test of the latency on your CPU. It should be very fast."

print("Generating...")
start = time.time()

# 'af_sarah' is a great standard voice. 
# Other options in the bin: af_bella, am_michael, bm_lewis, etc.
samples, sample_rate = kokoro.create(
    text, 
    voice="af_sarah", 
    speed=1.0, 
    lang="en-us"
)

end = time.time()
print(f"Generated in {end - start:.4f}s")

# Create tests directory if it doesn't exist
os.makedirs("tests", exist_ok=True)

# Save to verify
sf.write("tests/test_audio.wav", samples, sample_rate)
print("Saved to tests/test_audio.wav")

def speak_text(text):
    print(f"Generating: {text}")
    
    # This generates the audio numbers in RAM
    samples, sample_rate = kokoro.create(
        text, 
        voice="af_sarah", 
        speed=1.0, 
        lang="en-us"
    )
    
    # Play immediately without saving
    sd.play(samples, sample_rate)
    
    # Optional: Wait for audio to finish before continuing
    sd.wait() 

# Usage
speak_text("I am reading this directly from memory. No hard drive involved.")