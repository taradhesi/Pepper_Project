# script with the local whisper API for TTS and server communication
#communicates with the python 3 server 
#python 3

import requests  # to make HTTP requests to the flask server to communicate with python3 server
import speech_recognition as sr  # for mic input
import json  # for passwords
import time  # controls timing of responses
import difflib  # for matching passwords to similar inputs
import os  # file handling
import re  # cleans input
import bcrypt  # for hashing passwords

SERVER_IP = "127.0.0.1"  # localhost IP address for flask communication
PORT = 5000
TEXT_OUTPUT = "latest_response.txt"  # stores latest responses from pepper

#function to load known passwords
def load_known_passwords():
    try:
        with open("password_map.json", "r") as f:
            data = json.load(f)
            return list(data.keys()), data #returns list of passwords
    except:
        return [], {} #returns empty list if the file doesnt exist

#saves something for Pepper to say
def say(text):
    clean = ''.join([c if ord(c) < 128 else ' ' for c in text]) #removes random symbols
    with open(TEXT_OUTPUT, "w") as f:
        f.write(clean)
    print(f"Pepper says: {clean}") #clean text for pepper to smoothly say
    time.sleep(1.5)  #allows time for Pepper to finish speaking before continuing

#function to match to known password to help make the password recognition easier
def match_password(spoken, known_passwords):
    spoken = spoken.replace("sunshine please", "sunshine").replace("sunshine yeah", "sunshine").strip()

    if spoken == "sunshine":
        return "sunshine"  # Directly match 'sunshine'
    
    #gets close matches to the password
    matches = difflib.get_close_matches(spoken, known_passwords, n=1, cutoff=0.6)
    return matches[0] if matches else None

#rejects invalid stuff
def is_valid_transcription(text):
    if not text:
        return False
    if len([ch for ch in text if ord(ch) > 127]) > 10:
        return False
    return True

# Whisper STT input with a longer timeout and better error handling
def get_speech_input(timeout=20):
    recogniser = sr.Recogniser()
    with sr.Microphone() as source:
        print("Listening for input...")
        try:
            audio = recogniser.listen(source, timeout=15, phrase_time_limit=timeout) 
            print("Audio captured.")
        except sr.WaitTimeoutError:
            print("Listening timed out, no speech detected.")
            return ""
    try:
        text = recogniser.recognise_whisper(audio).strip().lower()  # Whisper recogniser
        print(f"Whisper heard: {text}")
        if is_valid_transcription(text):
            return text
        else:
            print("Whisper heard invalid transcription.")
            return ""
    except Exception as e:
        print(f"Whisper couldn't recognise speech: {e}")
    return ""

#function to match yes
def is_affirmative(response):
    return any(word in response.lower() for word in [
        "yes", "yeah", "yep", "correct", "that’s right", "yes.", "yes pepper"
    ])

#function to check for yes/no
def get_confirmation():
    confirmation = get_speech_input(timeout=8)
    if confirmation:
        print(f"Whisper heard: {confirmation}")
        if is_affirmative(confirmation):  # Checks if the response is affirmative
            return True
    return False

#Init user session
def init_user(password):
    try:
        response = requests.post(
            f"http://{SERVER_IP}:{PORT}/init",
            json={"user": password}
        )
        return response.json() #returns servers reply
    except Exception as e:
        return {"response": "Error: " + str(e), "status": "error"} #error handling

#Sends message to GPT
def chat_with_gpt(user_password, user_input):
    try:
        #Ensures user input isn't empty
        if not user_input.strip():
            return "Sorry, I didn't catch that. Could you repeat?"  # Handle empty input gracefully

        response = requests.post(
            f"http://{SERVER_IP}:{PORT}/chat",
            json={"user": user_password, "message": user_input}
        )
        if response.status_code == 200:
            response_text = response.json().get("response", "")
            if not response_text:
                return "Sorry, I didn't catch that. Could you repeat?"  # Handle empty response
            return response_text
        else:
            print(f"Server returned error: {response.status_code}")
            return "Server error occurred."
    except Exception as e:
        print(f"Error during server request: {e}")
        return "Error: " + str(e)

#Shortens long responses to a max length- stops overlapping with the users speech and listneing
def shorten_response(response, max_length=35):  #number of words allowed is 35
    words = response.split()
    if len(words) > max_length:
        return ' '.join(words[:max_length]) + "..."
    return response

#Function to calculate the listening delay based on the word count
def calculate_delay(response):
    word_count = len(response.split())
    delay = word_count * 0.35  # 0.35 seconds per word
    return delay + 1  # Add 1 second bufferjust incase

#wait for response to be finished before listening
def wait_for_response_to_finish(response):
    delay_time = calculate_delay(response)
    print(f"Waiting for {delay_time} seconds before listening.")
    time.sleep(delay_time)

#main password loop
def main():
    say("Hello! I'm ready to chat. Please say your password.")
    known_passwords, password_map = load_known_passwords()

    password = None
    retries = 0
    while not password and retries < 4: #retires<4 before asking for keyboard input
        spoken = get_speech_input()
        if not spoken:
            say("Could you repeat that? I didn't catch it the first time.")
            retries += 1
            continue

        matched = match_password(spoken, known_passwords)
        if matched:
            say(f"Did you say {matched}? Say yes or no.")
            if get_confirmation():
                password = matched  # Sets the password if confirmed
                break
            else:
                say("Okay, try again.")
        else:
            say("Could not match password. Try again.")
        retries += 1
#keyboard fallback
    if not password:
        say("Sorry, I couldn't hear you clearly. Please type your password.")
        password_input = input("Type your password: ").strip().lower() #makes password lowercase
        matched = match_password(password_input, known_passwords)
        if matched:
            print(f"Matched typed password: {matched}")
            password = matched
#if password is still not correct/registered: 
    if not password:
        say("Sorry, still couldn’t recognise you. Exiting.")
        return

#starts session with the server
    result = init_user(password)
    say(result["response"])

    silence_counter = 0
    while True:
        
        print("You can now speak.")
        user_input = get_speech_input(timeout=30)  #increased timeout for the game for decision making

#if no input at all
        if not user_input:
            say("Could you repeat that? I didn’t catch it the first time.")
            print("You can also type your message here if needed.")
            user_input = input("Type instead (or press Enter to skip): ").strip().lower()
            if not user_input:
                silence_counter += 1
                if silence_counter == 2:
                    say("Are you still there?")
                elif silence_counter >= 3:
                    say("Okay, I'll stop listening now. Goodbye!")
                    break
                continue

#counter resets if user speaks
        silence_counter = 0
        print(f"You: {user_input}")

        #only suggests "Would You Rather" when the user says "Let's play a game"
        if "let's play a game" in user_input.lower():
            say("Let's play 'Would You Rather'!")
            response = chat_with_gpt(password, "let's play a game")
            response = shorten_response(response)  #shorten the response
            say(response)
            wait_for_response_to_finish(response)  # Waits before listening again
            continue  # Skips normal conversation and go straight to game handling

        # Check for farewell
        farewell_keywords = ["bye", "goodbye", "exit"]
        if any(word in user_input.lower() for word in farewell_keywords):
            say("Did you mean to end our conversation? Please say yes Pepper or no Pepper.")
            confirmation = get_speech_input(timeout=8)
            if confirmation and is_affirmative(confirmation):
                say("Goodbye! If you ever feel like chatting again, I’ll be here. Take care!")
                break
            else:
                say("Okay! Glad you're still here.")
                continue

        response = chat_with_gpt(password, user_input)
        print(f"Pepper (will speak): {response}")
        response = shorten_response(response)  #Shortens the response
        say(response)
        wait_for_response_to_finish(response)  #waits before listening again

if __name__ == "__main__":
    main()

