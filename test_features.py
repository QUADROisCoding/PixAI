import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

from assistant import Assistant

class MockTTS:
    def speak(self, text):
        print(f"[TTS] {text}")

def test_assistant():
    tts = MockTTS()
    assistant = Assistant(tts=tts)
    
    test_queries = [
        "Wie spät ist es?",
        "Welcher Tag ist heute?",
        "Suche nach der Hauptstadt von Frankreich",
        "Wer ist der Präsident der USA?",
        "Starte die Kamera",
        "Was siehst du?",
        "Kamera aus",
        "Wie ist das Wetter in Berlin?"
    ]
    
    print("--- Pixel Assistant Feature Verification ---")
    for query in test_queries:
        print(f"\nUser: {query}")
        response = assistant.process_query(query)
        print(f"Assistant: {response}")

if __name__ == "__main__":
    test_assistant()
