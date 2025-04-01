# -*- coding: utf-8 -*-
# uses Whisper or keyboard input, sends to GPT server, and makes Pepper speak
#actually needs to be done in python 3 because speech recog is not supported by 2.7
import requests
import speech_recognition as sr
from naoqi import ALProxy


SERVER_IP = "127.0.0.1"
PORT = 5000
ROBOT_IP = "192.168.0.13"  
PEPPER_PASSWORD = "sunshine"  #registered user password

#Pepper TTS
tts = ALProxy("ALTextToSpeech", ROBOT_IP, 9559)

# Removes non-ASCII characters for Pepper's voice
def clean_for_tts(text):
    return ''.join([c if ord(c) < 128 else ' ' for c in text])

# Communicates with GPT server
def chat_with_gpt(user_password, user_input):
    try:
        response = requests.post(
            "http://{}:{}/chat".format(SERVER_IP, PORT),
            json={"user": user_password, "message": user_input}
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return "Sorry, the server is not responding."
    except Exception as e:
        return "Error: " + str(e)

# Gets spoken input from laptop mic using Whisper
def get_speech_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source, phrase_time_limit=6)
    try:
        return recognizer.recognize_whisper(audio)
    except Exception:
        return ""

# Main section
def main():
    print("Interaction started.")
    tts.say("Hello. I'm ready to chat with you.")

    while True:
        tts.say("Please speak now or type.")
        user_input = get_speech_input()

        if not user_input:
            try:
                user_input = raw_input("You (typed): ")
            except KeyboardInterrupt:
                print("Exiting.")
                break

        print("You: " + user_input)
        response = chat_with_gpt(PEPPER_PASSWORD, user_input)
        print("Pepper: " + response)

        safe_response = clean_for_tts(response)
        tts.say(safe_response)

if __name__ == "__main__":
    main()
