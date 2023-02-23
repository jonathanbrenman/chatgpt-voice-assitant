from gtts import gTTS
from dotenv import load_dotenv
from vosk import Model, KaldiRecognizer

import os
import requests
import json
import pyaudio
from playsound import playsound
from os import environ

language = "es" # Default language spanish (es).
OPEN_IA_URL = "https://api.openai.com/v1"

# Load environment variables
load_dotenv()
if "OPEN_IA_TOKEN" not in environ or environ.get("OPEN_IA_TOKEN") == "":
    print("OPEN_IA_TOKEN not found in .env")
    exit(1)

# Start listening with the selected voice model
def start_listening():
    voices_dir = "./voice-models/" + language

    if not os.path.exists(voices_dir):
        print("Voice model not found: " + language + " please download from: https://alphacephei.com/vosk/models and place it in " + voices_dir)
        exit(1)

    model = Model(voices_dir)
    recognizer = KaldiRecognizer(model, 16000)

    mic = pyaudio.PyAudio()
    stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
    stream.start_stream()
    return stream, recognizer

# Request to open_ia api completations
def ask_to_open_ia(message):
    if message == "":
        return None
    
    token = environ.get("OPEN_IA_TOKEN")
    url = OPEN_IA_URL + "/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    data = {
        "top_p": 1,
        "stop": "```",
        "prompt": message,
        "suffix": "\n```",
        "temperature": 0,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "max_tokens": 1000,
        "model": "text-davinci-003"
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_json = json.loads(response.text)
        response_text = response_json["choices"][0]["text"]
        return response_text
    except Exception as e:
        print(e)
        exit(1)

def speechToText(text):
    filename = "response_audio.mp3"
    myobj = gTTS(text=text, lang=language, slow=False)
    myobj.save(filename)
    playsound(filename)
    os.remove("./" + filename)

# Here Start Main Code
shouldOpenListening = False

while True:
    if shouldOpenListening is False:
        shouldOpenListening = True
        stream, recognizer = start_listening()
    
    data = stream.read(4096)
    
    if recognizer.AcceptWaveform(data):
        text = recognizer.Result()
        message = text[14:-3]

        if message == "":
            continue

        stream.stop_stream()
        stream.close()
        shouldOpenListening = False
        
        # Break the loop with those words
        if message == "salir" or message == "exit":
            break

        print("I've heard: " + message)
        
        # Ask chatgpt
        result = ask_to_open_ia(message)
        if result == None:
            continue

        print("This was the result from chatgpt: " + result)
        
        # Read the result
        speechToText(result)