# -*- coding: utf-8 -*-
# this file is no longer used but is the inital code for setting up new users for admin
# Python 2.7 client for Pepper
# Lets Pepper speak and listen to user, sending messages to Python 3 server

import requests 
import time
from naoqi import ALProxy

# Configuration
SERVER_IP = "127.0.0.1"  #laptop IP
PORT = 5000
ROBOT_IP = "192.168.0.13"  #Pepper IP 

# Setup proxies
tts = ALProxy("ALTextToSpeech", ROBOT_IP, 9559)
stt = ALProxy("ALSpeechRecognition", ROBOT_IP, 9559)
memory = ALProxy("ALMemory", ROBOT_IP, 9559)

# Vocabulary Pepper can recognize 
#no longer needed as we are now using whisper API script and STT
vocabulary = [
    "star", "tara", "martin", "alex", "james","sunshine", "moonlight",  # possible passwords
    "hi", "hello", "yes", "no", "stop", "play", "help", "bye",  # basic conversation
    "i feel sad", "i feel anxious", "i feel tired", "can we talk",
    "tell me something nice", "i'm okay", "i'm not okay", "give me advice",
    "thank you", "make me smile", "i had a bad day"
]
stt.pause(True) #pause peppers speech to update vocab
stt.setVocabulary(vocabulary, False)
stt.pause(False) #resuem

#Cleans peppers speech
def safe_say(text):
    clean = ''.join([c if ord(c) < 128 else ' ' for c in text])
    tts.say(clean)

# Function to listen for a spoken word/phrase
def listen():
    stt.subscribe("pepper_listener") #pepper starts listening
    print("Listening...")
    time.sleep(4) #waits 4 seconds
    word = memory.getData("WordRecognized") #gets the word Pepper heard
    stt.unsubscribe("pepper_listener") # stops listneing
    if word and isinstance(word, list) and len(word) > 0: 
        return word[0].strip().lower() #males word lowercase
    else:
        return "" #return empty if nothing was heard 

# Communicate with Python 3 server
def init_user(user_password):
    try:
        #sends the POST request to the server with the users passwordd and if the server works, the response text is returned
        response = requests.post(
            "http://{}:{}/init".format(SERVER_IP, PORT),
            json={"user": user_password}
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return "Error: Could not initialize user."
    except Exception as e:
        return "Error: " + str(e) #error handling

#function to send users speech input to the server for a response
def chat_with_gpt(user_password, user_input):
    try:
        #sends POST request with the password and input
        response = requests.post(
            "http://{}:{}/chat".format(SERVER_IP, PORT),
            json={"user": user_password, "message": user_input}
        )
        if response.status_code == 200: #if works,returns reply
            return response.json()["response"]
        else:
            return "Error: AI server not responding."
    except Exception as e:
        return "Error: " + str(e) #error handling

# Main password loop
def main():
    safe_say("Welcome. Please say your password.")
    while True:
        password = listen()
        print("Recognized password:", password)
        response = init_user(password)
        if "Welcome back" in response:
            safe_say(response)
            break #exits the password loop and begins conversation
        else:
            safe_say("Sorry, I didn't recognize that. Let's try again.")

#main conversation loop
    while True:
        safe_say("I'm listening. Please speak.")
        user_input = listen()
        if user_input:
            print("You:", user_input)
            response = chat_with_gpt(password, user_input)
            print("Pepper:", response)
            safe_say(response)
        else:
            safe_say("Sorry, I didn't catch that.")

if __name__ == "__main__": #starts main program
    main()
