import os
import re
import requests
from urllib.parse import quote
import server # Web Interface
from groq import Groq
from skills.timer import TimerManager
from skills.camera import CameraManager
from config import OPENWEATHER_API_KEY, DEFAULT_CITY, WETTER_KEYWORDS
from datetime import datetime

class Assistant:
    def __init__(self, tts=None):
        self.timer_manager = TimerManager(tts) if tts else None
        self.camera_manager = CameraManager(tts) if tts else None

    def process_query(self, text):
        """Determine intent and get response"""
        text_lower = text.lower()
        
        if self.timer_manager:
            # Timer / Wecker / Countdown
            # Matches: "Stelle einen Timer/Wecker auf 5 Minuten"
            timer_trigger = any(x in text_lower for x in ["timer", "wecker", "countdown"])
            timer_match = re.search(r'(\d+)\s+(minute|minuten|sekunde|sekunden|stunde|stunden)', text_lower)
            
            if timer_trigger and timer_match:
                amount = timer_match.group(1)
                unit = timer_match.group(2)
                return self.timer_manager.set_timer(amount, unit)
            
            # Stopwatch / Stoppuhr
            if "stoppuhr" in text_lower or "stopwatch" in text_lower:
                if any(x in text_lower for x in ["start", "los", "go"]):
                    return self.timer_manager.start_stopwatch()
                elif any(x in text_lower for x in ["stop", "stopp", "ende", "halt", "aus"]):
                    return self.timer_manager.stop_stopwatch()
        
        # Check for Time Intent
        time_keywords = ["spät", "uhr", "zeit", "clock", "time", "datum", "welcher tag"]
        if any(x in text_lower for x in time_keywords) and not any(x in text_lower for x in ["timer", "wecker", "countdown", "stoppuhr"]):
            return self.get_time()
        
        # Check for Web Search Intent
        search_trigger = any(x in text_lower for x in ["suche", "suche nach", "finde", "googlen", "search for", "search", "im internet", "wer ist", "was ist"])
        if search_trigger and not any(x in text_lower for x in ["wetter", "uhr", "zeit", "kamera", "benachrichtigung"]):
            # Remove trigger words and search
            query = text_lower
            for trigger in ["suche nach", "suche", "finde", "googlen", "search for", "search", "im internet", "wer ist", "was ist"]:
                query = query.replace(trigger, "").strip()
            if query:
                return self.web_search(query)
        
        # Check for Notification Intent
        # "Sende Benachrichtigung an Handy: Hallo Welt"
        if "benachrichtigung" in text_lower or "send notification" in text_lower:
            parts = text.split(":", 1)
            msg = "Test"
            target = "Mobile" 
            
            if len(parts) > 1:
                msg = parts[1].strip()
            
            if "pc" in text_lower: target = "PC"
            
            count = server.send_notification(target, msg)
            if count > 0:
                return f"Benachrichtigung an {target} gesendet."
            else:
                return f"Kein {target} verbunden."

        # Check for weather
        for keyword in WETTER_KEYWORDS:
            if keyword in text_lower:
                return self.get_weather(text)
        
        # Check for Camera Intent
        if self.camera_manager:
            if any(x in text_lower for x in ["starte kamera", "kamera starten", "öffne kamera", "camera start", "kamera an"]):
                return self.camera_manager.start_camera()
            elif any(x in text_lower for x in ["stoppe kamera", "kamera stoppen", "schließe kamera", "camera stop", "kamera aus"]):
                return self.camera_manager.stop_camera()
            elif any(x in text_lower for x in ["was siehst du", "erkennen", "identifizieren", "was ist das", "siehe", "detect", "identify"]):
                return self.camera_manager.describe_scene()
        
        # Default to AI
        return self.get_ai_response(text)

    def get_weather(self, text):
        if not OPENWEATHER_API_KEY:
            return "Ich habe keinen OpenWeather API-Schlüssel gefunden."

        # Simplistic city extraction (better with NER, but regex is okay for now)
        city = DEFAULT_CITY
        # Try to find city in text (very basic check)
        words = text.split()
        if "in" in words:
            try:
                city_idx = words.index("in") + 1
                if city_idx < len(words):
                    city = words[city_idx].strip("?.!,")
            except:
                pass

        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=de"
            response = requests.get(url)
            data = response.json()
            
            if response.status_code != 200:
                print(f"Weather Error: {data}")
                return f"Ich konnte das Wetter für {city} nicht abrufen."

            temp = round(data['main']['temp'])
            desc = data['weather'][0]['description']
            return f"Das Wetter in {city}: {desc} bei {temp} Grad Celsius."

        except Exception as e:
            print(f"Weather Exception: {e}")
            return "Es gab einen Fehler beim Abrufen des Wetters."

    def get_time(self):
        """Return current time"""
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        date_str = now.strftime("%d.%m.%Y")
        days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        day_name = days[now.weekday()]
        return f"Es ist {time_str} Uhr am {day_name}, den {date_str}."

    def web_search(self, query):
        """Perform web search using DuckDuckGo"""
        try:
            # Using DuckDuckGo Lite for easier parsing
            url = f"https://duckduckgo.com/lite/?q={quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return "Die Suche konnte nicht durchgeführt werden."
            
            content = response.text
            
            # Find results in DuckDuckGo Lite
            # Links are usually in <a class="result-link" href="...">...</a>
            import re as re_module
            pattern = r'<a[^>]*class="result-link"[^>]*>([^<]*)</a>'
            matches = re_module.findall(pattern, content)
            
            results = []
            for i, title in enumerate(matches[:3]):
                title = title.strip()
                if title:
                    results.append(f"- {title}")
            
            if results:
                summary = f"Ich habe im Internet nach '{query}' gesucht. Hier sind einige Ergebnisse:\n" + "\n".join(results)
                return summary
            else:
                return f"Ich habe keine direkten Ergebnisse für '{query}' gefunden."
                
        except Exception as e:
            print(f"Web Search Exception: {e}")
            return "Es gab einen Fehler bei der Websuche."

    def get_ai_response(self, text):
        if not os.getenv("GROQ_API_KEY"):
            return "Ich habe keinen Groq API-Schlüssel gefunden. Bitte setze GROQ_API_KEY in der .env Datei."

        try:
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Du bist Pixel, ein hilfreicher KI-Assistent. Antworte kurz und prägnant auf Deutsch."},
                    {"role": "user", "content": text}
                ],
                model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            )
            
            return chat_completion.choices[0].message.content

        except Exception as e:
            print(f"AI Exception: {e}")
            return "Es gab einen Fehler bei der Verbindung zu Groq. Überprüfe deinen API-Schlüssel."
