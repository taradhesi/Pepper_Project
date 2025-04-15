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

# Load known passwords
def load_known_passwords():
    try:
        with open("password_map.json", "r") as f:
            data = json.load(f)
            return list(data.keys()), data
    except:
        return [], {}

# Save something for Pepper to say
def say(text):
    clean = ''.join([c if ord(c) < 128 else ' ' for c in text])
    with open(TEXT_OUTPUT, "w") as f:
        f.write(clean)
    print(f"Pepper says: {clean}")
    time.sleep(1.5)  # Allows time for Pepper to finish speaking before continuing

# Match to known password
def match_password(spoken, known_passwords):
    spoken = spoken.replace("sunshine please", "sunshine").replace("sunshine yeah", "sunshine").strip()

    if spoken == "sunshine":
        return "sunshine"  # Directly match 'sunshine'
    
    matches = difflib.get_close_matches(spoken, known_passwords, n=1, cutoff=0.6)
    return matches[0] if matches else None

# Filter out junk transcriptions (We will allow short responses now)
def is_valid_transcription(text):
    if not text:
        return False
    if len([ch for ch in text if ord(ch) > 127]) > 10:
        return False
    return True

# Whisper STT input with a longer timeout and better error handling
def get_speech_input(timeout=20):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for input...")
        try:
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=timeout)
            print("Audio captured.")
        except sr.WaitTimeoutError:
            print("Listening timed out — no speech detected.")
            return ""
    try:
        text = recognizer.recognize_whisper(audio).strip().lower()  # Whisper recognizer
        print(f"Whisper heard: {text}")
        if is_valid_transcription(text):
            return text
        else:
            print("Whisper heard invalid transcription.")
            return ""
    except Exception as e:
        print(f"Whisper couldn't recognize speech: {e}")
    return ""

# Loosely match yes
def is_affirmative(response):
    return any(word in response.lower() for word in [
        "yes", "yeah", "yep", "correct", "that’s right", "yes.", "yes pepper"
    ])

# Define get_confirmation function to check for 'yes' or 'no'
def get_confirmation():
    confirmation = get_speech_input(timeout=8)
    if confirmation:
        print(f"Whisper heard: {confirmation}")
        if is_affirmative(confirmation):  # Checks if the response is affirmative
            return True
    return False

# Init user session
def init_user(password):
    try:
        response = requests.post(
            f"http://{SERVER_IP}:{PORT}/init",
            json={"user": password}
        )
        return response.json()
    except Exception as e:
        return {"response": "Error: " + str(e), "status": "error"}

# Send message to GPT
def chat_with_gpt(user_password, user_input):
    try:
        # Ensure user input isn't empty
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

# Shortens long responses to a maximum length
def shorten_response(response, max_length=35):  # max_length is the number of words allowed
    words = response.split()
    if len(words) > max_length:
        return ' '.join(words[:max_length]) + "..."
    return response

# Function to calculate the listening delay based on word count
def calculate_delay(response):
    word_count = len(response.split())
    delay = word_count * 0.35  # 0.3 seconds per word
    return delay + 1  # Add 1 second buffer

# Wait for response to be finished before listening
def wait_for_response_to_finish(response):
    delay_time = calculate_delay(response)
    print(f"Waiting for {delay_time} seconds before listening.")
    time.sleep(delay_time)

# MAIN Loop
def main():
    say("Hello! I'm ready to chat. Please say your password.")
    known_passwords, password_map = load_known_passwords()

    password = None
    retries = 0
    while not password and retries < 4:
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

    if not password:
        say("Sorry, I couldn't hear you clearly. Please type your password.")
        password_input = input("Type your password: ").strip().lower()
        matched = match_password(password_input, known_passwords)
        if matched:
            print(f"Matched typed password: {matched}")
            password = matched

    if not password:
        say("Sorry, still couldn’t recognise you. Exiting.")
        return

    result = init_user(password)
    say(result["response"])

    silence_counter = 0
    while True:
        
        print("You can now speak.")
        user_input = get_speech_input(timeout=30)  # Increased timeout for game

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

        silence_counter = 0
        print(f"You: {user_input}")

        # Only suggest "Would You Rather" when the user says "Let's play a game"
        if "let's play a game" in user_input.lower():
            say("Let's play 'Would You Rather'!")
            response = chat_with_gpt(password, "let's play a game")
            response = shorten_response(response)  # Shorten the response
            say(response)
            wait_for_response_to_finish(response)  # Wait before listening again
            continue  # Skip normal conversation and go straight to game handling

        # Check for possible farewell
        farewell_keywords = ["bye", "goodbye", "exit"]
        if any(word in user_input.lower() for word in farewell_keywords):
            say("Did you mean to end our conversation? Please say yes Pepper or no Pepper.")
            confirmation = get_speech_input(timeout=8)
            if confirmation and is_affirmative(confirmation):
                say("Goodbye! If you ever feel like chatting again, I’ll be here for you. Take care!")
                break
            else:
                say("Okay! Glad you're still here.")
                continue

        response = chat_with_gpt(password, user_input)
        print(f"Pepper (will speak): {response}")
        response = shorten_response(response)  # Shorten the response
        say(response)
        wait_for_response_to_finish(response)  # Wait before listening again

if __name__ == "__main__":
    main()

