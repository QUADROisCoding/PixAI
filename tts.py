import edge_tts
import pygame
import asyncio
import threading
import os
import time
import server # Web Interface

class TextToSpeech:
    def __init__(self):
        self.voice = "de-DE-ConradNeural"  # High quality German male voice
        # Alternative: "de-DE-KatjaNeural" (Female)
        
        # Initialize pygame mixer for audio playback
        try:
            pygame.mixer.init()
        except:
            print("Warning: Pygame mixer failed to initialize")
        
        self.lock = threading.Lock()
        self.temp_file = "temp_speech.mp3"

    def speak(self, text):
        """Speak text in a separate thread to avoid blocking"""
        thread = threading.Thread(target=self._speak_thread, args=(text,))
        thread.start()

    def _speak_thread(self, text):
        with self.lock:
            try:
                # Notify Web Interface
                server.emit_status('speaking', text)
                
                # generate audio using async loop
                asyncio.run(self._generate_audio(text))
                
                # play audio
                self._play_audio()
                
                # Back to idle
                server.emit_status('idle')
            except Exception as e:
                print(f"TTS Error: {e}")
                server.emit_status('idle')  # Ensure idle on error

    async def _generate_audio(self, text):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(self.temp_file)

    def _play_audio(self):
        if not os.path.exists(self.temp_file):
            return

        try:
            pygame.mixer.music.load(self.temp_file)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            # Unload to release file
            pygame.mixer.music.unload()
            
        except Exception as e:
            print(f"Playback Error: {e}")
        
        # Cleanup
        try:
            if os.path.exists(self.temp_file):
                os.remove(self.temp_file)
        except:
            pass

if __name__ == "__main__":
    tts = TextToSpeech()
    print("Testing TTS...")
    tts.speak("Hallo! Das ist meine neue, menschliche Stimme.")
    # Keep main thread alive to hear it
    time.sleep(5)
