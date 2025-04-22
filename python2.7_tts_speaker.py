
# -*- coding: utf-8 -*-
# Python 2.7 script to let Pepper speak responses saved from Whisper + GPT

import time  # controls timing of speech and any delays
import os  # for file handling
from naoqi import ALProxy  # Pepper

PEPPER_IP = "192.168.0.13"  # Peppers IP address
TTS = ALProxy("ALTextToSpeech", PEPPER_IP, 9559)

RESPONSE_FILE = "latest_response.txt"  # Text file updated by Whisper script that gives pepper the latest message to speak

# Reads the file containing the message for Pepper to speak
def read_response():
    if os.path.exists(RESPONSE_FILE):
        with open(RESPONSE_FILE, "r") as f:
            response = f.read().strip()  # reads the file and removes extra whitespace
            if response:  # check that there is some response to return
                return response
    return None  # if the file doesnt exist or is empty

# Cleans text for TTS (removes non-ASCII characters)
def clean_text(text):
    return ''.join([c if ord(c) < 128 else ' ' for c in text])  # replaces any character that has a non-ASCII value with a space

# Speaks the text using Pepper's TTS system
def speak_text(text):
    safe_text = clean_text(text)  # removes non-ASCII chars
    print("Pepper will say:", safe_text)
    TTS.say(safe_text)

    # Calculate the approximate time needed to speak the text (estimated at 1 second per 10 characters)
    speak_duration = len(safe_text) / 10  # Adjust this factor as necessary based on how fast Pepper speaks
    print("Pepper will take approximately {} seconds to speak.".format(speak_duration))
    
    time.sleep(speak_duration + 1)  # Wait for Pepper to finish speaking before listening

# MAIN Loop to continuously listen for new responses
def main():
    print("Pepper TTS listener is active...")
    last_spoken = ""  # variable to keep track of the last spoken response to avoid repeating the same messages
    
    while True:  # Infinite loop for checking for new responses
        try:
            # Check for a new response in latest response file
            response = read_response()
            if response and response != last_spoken:  # Only speak if the response is new
                # If the response is valid and different from the last one, speak it
                if "server not responding" not in response.lower():  # Avoid speaking error messages
                    speak_text(response)  # Speak the response
                    last_spoken = response  # Save the spoken response to avoid repeating it
            time.sleep(1)  # Wait before checking for a new response again
        except Exception as e:
            print("Error occurred: ", e)
            time.sleep(2)  # Wait before trying again in case of an error

# Run main script
if __name__ == "__main__":
    main()  # calls main function to start the program
