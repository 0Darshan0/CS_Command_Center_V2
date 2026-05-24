import os
from config import GEMINI_API_KEY
from google import genai

print("1. Initializing Gemini Client...")
# We add a 15-second timeout to force it to fail instead of hanging forever
client = genai.Client(api_key=GEMINI_API_KEY, http_options={'timeout': 15000})

print("2. Sending test prompt to Gemini 1.5 Flash...")
try:
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents='Respond with a single word: Hello!'
    )
    print("3. ✅ SUCCESS! Gemini says:", response.text)
except Exception as e:
    print("3. ❌ FAILED! Error:", e)