# Speech To Text (STT)

This folder contains different implementations of Speech To Text pipelines. 

Two of these use [Deepgram](https://developers.deepgram.com/home), one uses Whisper from OpenAI. 

Using Deepgram we can directly stream and reduce latency: Whisper needs files to transcribe, so must first save to files and then transcribe -> high latency (but also, hig accuracy). 

Key differences: 

- Deepgram `Nova3`: streaming transcription model, efficient
- Deepgram `Flux`: AI transcription model, automatically detects pauses: perfect for voice agents
- OpenAI's `Whisper`: high accuracy, does not stream -> high latency