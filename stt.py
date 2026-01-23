import speech_recognition as sr
import threading
import os
import io
from groq import Groq

class SpeechToText:
    def __init__(self, on_data):
        self.on_data = on_data
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.stop_listening = None

    def start_stream(self):
        print("Calibrating microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
        print("Microphone active...")
        # starts a background thread
        self.stop_listening = self.recognizer.listen_in_background(
            self.microphone, 
            self._callback,
            phrase_time_limit=10
        )

    def _callback(self, recognizer, audio):
        try:
            # Get WAV data instead of letting recognizer choose format (Google needs FLAC)
            wav_data = audio.get_wav_data()
            
            # Use Groq Whisper for transcription
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            
            # Wrap bytes in a file-like object
            audio_file = io.BytesIO(wav_data)
            audio_file.name = "speech.wav" # Groq needs a filename extension
            
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                language="de", # Forcing German as in previous implementation
                response_format="text"
            )
            
            text = transcription.strip()
            if not text:
                return

            print(f"STT: {text}")
            
            # Create a mock object similar to AssemblyAI's structure for compatibility
            class Transcript:
                def __init__(self, text):
                    self.text = text
            
            # Pass to main callback
            self.on_data(Transcript(text))
            
        except Exception as e:
            print(f"STT Error: {e}")

    def stop_stream(self):
        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)

if __name__ == "__main__":
    def on_data(transcript):
        print(f"Heard: {transcript.text}")

    stt = SpeechToText(on_data)
    try:
        stt.start_stream()
        import time
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        stt.stop_stream()
