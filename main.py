# import assemblyai as aai # Removed
from stt import SpeechToText
from tts import TextToSpeech
from assistant import Assistant
import time
import threading
import colorama
import server # Web Interface
from colorama import Fore, Style

colorama.init()

print(f"{Fore.CYAN}Pixel AI Assistant (Python) is starting...{Style.RESET_ALL}")
print(f"{Fore.CYAN}Say 'Pixel' to wake me up.{Style.RESET_ALL}")

tts = TextToSpeech()
assistant = Assistant(tts=tts)

# Wake word state
is_active = False

def on_data(transcript):
    global is_active
    
    if not transcript.text:
        return

    # It's always a final transcript with SpeechRecognition
    text = transcript.text.strip()
    try:
        print(f"{Fore.GREEN}User: {text}{Style.RESET_ALL}")
    except:
        print(f"User: {text}")
    
    # Check for Wake Word "Pixel"
    if "pixel" in text.lower() or is_active:
        is_active = True 
        
        # Remove "Pixel" from start if present
        query = text
        lower_text = query.lower()
        if "pixel" in lower_text:
            # Simple split to get content after pixel
            parts = lower_text.split("pixel", 1)
            if len(parts) > 1 and parts[1].strip():
                # We need to preserve case, so match index
                idx = query.lower().index("pixel")
                query = query[idx+5:].strip()
            elif lower_text.strip() == "pixel":
                query = ""

        # If there's a query after "Pixel", process it
        if query:
            try:
                print(f"{Fore.YELLOW}Processing: {query}{Style.RESET_ALL}")
            except:
                pass
                
            response = assistant.process_query(query)
            try:
                print(f"{Fore.CYAN}Pixel: {response}{Style.RESET_ALL}")
            except:
                print(f"Pixel: {response}")
                
            tts.speak(response)
            is_active = False 
        else:
            # Just woke up
            print(f"{Fore.CYAN}Listening for command...{Style.RESET_ALL}")
            server.emit_status("listening", "Listening...")
            tts.speak("Ja?")

    # Debug: log ignored input
    elif not is_active and text:
        # Gray out the text to show it was heard but not processed
        print(f"{Style.DIM}Ignored: {text} (Say 'Pixel' to wake){Style.RESET_ALL}")

def start_web_server():
    server.start_server()

def main():
    # Setup Web Input Handler
    server.set_input_handler(on_data)

    # Start Web Interface in Background
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    stt = SpeechToText(on_data)
    
    print(f"{Fore.GREEN}[OK] System Online. Listening for 'Pixel'...{Style.RESET_ALL}")
    tts.speak("Pixel ist bereit.")
    
    try:
        stt.start_stream()
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Scaling down...{Style.RESET_ALL}")
        stt.stop_stream()

if __name__ == "__main__":
    main()
