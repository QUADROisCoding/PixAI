import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenRouter Config
# Groq Config
GROQ_MODEL = "llama-3.3-70b-versatile" # Very fast, high intelligence
# alternative: "llama3-8b-8192" for max speed

# Locations
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Berlin")

# German Weather Keywords
WETTER_KEYWORDS = [
    'wetter', 'temperatur', 'vorhersage', 'regen', 'sonnig', 'bewölkt',
    'heiß', 'kalt', 'wind', 'feuchtigkeit', 'schnee', 'sturm', 'grad',
    'celsius', 'warm', 'kühl', 'draußen', 'heute', 'morgen', 'woche',
    'regnet', 'scheint', 'sonne', 'wolken', 'gewitter', 'nebel', 'frost',
    'hitze', 'luftfeuchtigkeit', 'wetterbericht', 'prognose'
]
