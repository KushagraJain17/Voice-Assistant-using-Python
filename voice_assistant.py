import speech_recognition as sr
import pyttsx3
import webbrowser
import datetime
import os
import time
import threading

try:
    import pywhatkit
    import wikipedia
    import requests
    import pyjokes
except Exception:
    pywhatkit = None
    wikipedia = None
    requests = None
    pyjokes = None

CONFIG = {
    "WAKE_WORDS": ["hey assistant", "ok assistant", "assistant", "hello"],
    "NOTES_FILE": "assistant_notes.txt"
}

def speak(text: str):
    try:
        engine = pyttsx3.init('sapi5')
        engine.setProperty('rate', 160)
        voices = engine.getProperty('voices')
        if voices:
            engine.setProperty('voice', voices[0].id)
        # Add a slight pause for human-like effect
        text = text + '.'
        print("Assistant:", text)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print("Speech error:", e)

listener = sr.Recognizer()
mic = sr.Microphone()

def listen(timeout=None, phrase_time_limit=None) -> str:
    with mic as source:
        listener.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = listener.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            return ""
    try:
        text = listener.recognize_google(audio)
        return text.lower()
    except Exception:
        return ""

def is_wake_phrase(text):
    return any(w in text for w in CONFIG["WAKE_WORDS"])

def tell_time():
    t = datetime.datetime.now().strftime('%I:%M %p')
    speak(f"Right now, it is {t}")

def tell_date():
    d = datetime.date.today().strftime('%A, %d %B %Y')
    speak(f"Today is {d}")

def open_website(site):
    if not site.startswith('http'):
        site = 'https://' + site
    webbrowser.open(site)
    speak(f"Opening {site} for you")

def search_web(query):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    speak(f"Here’s what I found for {query}")

def play_youtube(query):
    if pywhatkit:
        try:
            pywhatkit.playonyt(query)
            speak(f"Playing {query} on YouTube. Enjoy!")
        except Exception:
            speak("Oops, I couldn't play that video.")
    else:
        search_web(query + ' site:youtube.com')

def get_wikipedia_summary(topic):
    if wikipedia:
        try:
            summary = wikipedia.summary(topic, sentences=2)
            speak(summary)
        except Exception:
            speak("Hmm, I couldn't find anything on that topic.")
    else:
        speak("Wikipedia feature is not available.")

def tell_joke():
    if pyjokes:
        speak(pyjokes.get_joke())
    else:
        speak("Sorry, I can't tell jokes right now. Install pyjokes.")

def take_note(text):
    with open(CONFIG['NOTES_FILE'], 'a', encoding='utf-8') as f:
        f.write(f"{datetime.datetime.now().isoformat()} - {text}\n")
    speak('Got it, I saved your note.')

def read_notes():
    if not os.path.exists(CONFIG['NOTES_FILE']):
        speak('You have no saved notes.')
        return
    with open(CONFIG['NOTES_FILE'], 'r', encoding='utf-8') as f:
        notes = f.read().strip()
    if notes:
        speak('Here are your notes:')
        speak(notes[:1000])
    else:
        speak('You have no notes to read.')

def set_timer(seconds):
    def timer_thread(sec):
        speak(f'Sure, I have set a timer for {sec} seconds.')
        time.sleep(sec)
        speak('Time’s up!')
    threading.Thread(target=timer_thread, args=(seconds,), daemon=True).start()

def calculate(expr):
    allowed = set('0123456789+-*/(). %')
    if all(ch in allowed for ch in expr):
        try:
            result = eval(expr, {'__builtins__': None}, {})
            speak(f'The answer is {result}')
        except Exception:
            speak('I had trouble calculating that.')
    else:
        speak('I cannot process that expression.')

def handle_command(cmd):
    cmd = cmd.strip()
    if not cmd:
        return
    if 'time' in cmd:
        tell_time()
    elif 'date' in cmd:
        tell_date()
    elif cmd.startswith('open '):
        open_website(cmd.replace('open ', ''))
    elif cmd.startswith('search for '):
        search_web(cmd.replace('search for ', ''))
    elif cmd.startswith('play '):
        play_youtube(cmd.replace('play ', ''))
    elif 'wikipedia' in cmd:
        get_wikipedia_summary(cmd.replace('wikipedia', ''))
    elif 'joke' in cmd:
        tell_joke()
    elif 'set timer for' in cmd:
        try:
            sec = int(cmd.split('set timer for ')[1].split()[0])
            set_timer(sec)
        except Exception:
            speak('Please tell me the timer duration in seconds.')
    elif cmd.startswith('note '):
        take_note(cmd.replace('note ', ''))
    elif 'read notes' in cmd:
        read_notes()
    elif cmd.startswith('calculate ') or cmd.startswith('what is '):
        expr = cmd.replace('calculate ', '').replace('what is ', '')
        calculate(expr)
    else:
        search_web(cmd)

def assistant_loop():
    speak('Hi! I am your assistant. You can call me anytime.')
    while True:
        text = listen(timeout=5, phrase_time_limit=4)
        if not text:
            continue
        if is_wake_phrase(text):
            speak('Yes, I am listening.')
            cmd = listen(timeout=8, phrase_time_limit=8)
            if cmd:
                speak(f'Got it. You said: {cmd}')
                handle_command(cmd)
            else:
                speak('I didn’t catch that. Could you repeat?')

if __name__ == '__main__':
    try:
        assistant_loop()
    except KeyboardInterrupt:
        speak('Goodbye! Talk to you later.')
