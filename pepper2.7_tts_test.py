# -*- coding: utf-8 -*-
# Python 2.7 client for Pepper with TTS and STT support
# Lets Pepper speak and listen to user, sending messages to Python 3 server
#THIS IS USING PEPPERS NAOQI TTS STT


import requests
import time
from naoqi import ALProxy


SERVER_IP = "127.0.0.1"  
PORT = 5000
ROBOT_IP = "192.168.0.13"  


tts = ALProxy("ALTextToSpeech", ROBOT_IP, 9559)
stt = ALProxy("ALSpeechRecognition", ROBOT_IP, 9559)
memory = ALProxy("ALMemory", ROBOT_IP, 9559)

# Expanded vocabulary for mental health conversations
mental_health_phrases = [
    "i feel sad", "i feel anxious", "i feel stressed", "i feel happy",
    "i feel tired", "i feel angry", "i feel lonely", "can we talk",
    "tell me something nice", "play a game", "tell me a joke", "i need help",
    "i'm okay", "i'm not okay", "i'm fine", "i'm not fine", "what should i do",
    "give me advice", "how are you", "thank you", "bye", "hello",
    "can we talk about something", "i want to talk", "you make me feel better",
    "i'm feeling overwhelmed", "i had a bad day", "i had a good day",
    "can we do something fun", "i want to talk to someone", "i want to be alone",
    "i’m feeling burnt out", "i feel like giving up", "nobody understands me",
    "i'm scared", "i'm worried", "i'm nervous", "what do you think",
    "can you cheer me up", "make me smile", "yes", "no", "i dont know", "i'm sad", "i'm happy",
    "sunshine", "galaxy", "pineapple", "supernova", "tara", "james", "alex", "hi", "play", "stop", "help", "martin", "star", "sunshine", "moonlight"
]
stt.pause(True)
stt.setVocabulary(mental_health_phrases, False)
stt.pause(False)

# sorts strings for responses

def clean_for_tts(text):
    return ''.join([c if ord(c) < 128 else ' ' for c in text])

# Sends a message to the Python 3 server
def chat_with_gpt(user_password, user_input):
    try:
        response = requests.post(
            "http://{}:{}/chat".format(SERVER_IP, PORT),
            json={"user": user_password, "message": user_input}
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return "Error: AI server not responding."
    except Exception as e:
        return "Error: " + str(e)

# Checks if user is registered
def init_user(user_password):
    try:
        response = requests.post(
            "http://{}:{}/init".format(SERVER_IP, PORT),
            json={"user": user_password}
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return "Error: Could not initialize user."
    except Exception as e:
        return "Error: " + str(e)

# Listens to the user's voice and return recognized word/phrase
def listen():
    stt.subscribe("pepper_listener")
    print("Listening...")
    time.sleep(4)  # Adjust as needed
    word = memory.getData("WordRecognized")
    stt.unsubscribe("pepper_listener")
    if word and isinstance(word, list) and len(word) > 0:
        return word[0]  # Return first recognized phrase
    else:
        return ""

# Main interaction
def main():
    tts.say("Welcome! Please say your password.")
    user_password = listen().strip().lower()
    print("Recognized password: [{}]".format(user_password))
    tts.say("I heard: " + user_password + ". Is that correct?")
    confirmation = listen().strip().lower()
    if confirmation != "yes":
        tts.say("Okay, let's try again. Please say your password.")
        user_password = listen().strip().lower()

    # keyboard fallback
    if user_password not in mental_health_phrases:
        tts.say("I did not recognize that password. Please type it instead.")
        user_password = raw_input("Enter password: ").strip().lower()

    init_message = init_user(user_password)
    print("Pepper: " + init_message.encode('utf-8'))
    tts.say(clean_for_tts(init_message))

    while True:
        tts.say("I am listening. Please speak.")
        user_input = listen()
        if user_input:
            print("You: " + user_input.encode('utf-8'))
            response = chat_with_gpt(user_password, user_input)
            print("Pepper: " + response.encode('utf-8'))
            tts.say(clean_for_tts(response))
        else:
            tts.say("Sorry, I did not catch that.")

if __name__ == "__main__":
    main()
