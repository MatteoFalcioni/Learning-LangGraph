import sounddevice as sd

def read_text(text, model):
    """
    Function to read out loud a given text with a Kokoro model. 
    """    
    # This generates the audio numbers in RAM
    samples, sample_rate = model.create(
        text, 
        voice="af_sarah", 
        speed=1.0, 
        lang="en-us"
    )
    
    # Play immediately without saving
    sd.play(samples, sample_rate)
    
    # Optional: Wait for audio to finish before continuing
    sd.wait() 
