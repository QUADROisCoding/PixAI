import threading
import time
import re

class TimerManager:
    def __init__(self, tts):
        self.tts = tts
        self.stopwatch_start = None

    def set_timer(self, duration, unit):
        seconds = 0
        if "second" in unit:
            seconds = int(duration)
        elif "minute" in unit:
            seconds = int(duration) * 60
        elif "hour" in unit:
            seconds = int(duration) * 3600
        
        # Start timer thread
        threading.Thread(target=self._timer_thread, args=(seconds,)).start()
        return f"Timer für {duration} {unit} gestellt."

    def _timer_thread(self, seconds):
        time.sleep(seconds)
        # Alarm / Announcement
        print("TIMER FINISHED!")
        self.tts.speak("Der Timer ist abgelaufen!")

    def start_stopwatch(self):
        self.stopwatch_start = time.time()
        return "Stoppuhr gestartet."

    def stop_stopwatch(self):
        if not self.stopwatch_start:
            return "Es läuft keine Stoppuhr."
        
        elapsed = time.time() - self.stopwatch_start
        self.stopwatch_start = None
        
        # Format output
        if elapsed < 60:
            return f"Zeit: {int(elapsed)} Sekunden."
        else:
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            return f"Zeit: {minutes} Minuten und {seconds} Sekunden."
