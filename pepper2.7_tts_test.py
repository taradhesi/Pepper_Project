#Pepper python 2.7 script running to hand Pepper's connection to the python 3 server and recieve the responses from Chatgpt.
#Allows pepper to speak to user

import time #for pauses and delays in pepper's speech
import os #for files
from naoqi import ALProxy #for TTS module

PEPPER_IP = "192.168.0.13"  #pepper's IP address
TTS = ALProxy("ALTextToSpeech", PEPPER_IP, 9559) 
RESPONSE_FILE = "latest_response.txt"  #text file updated by Whisper script for pepper to speak

#reads the file containing the message for Pepper to speak
def read_response():
    if os.path.exists(RESPONSE_FILE):
        with open(RESPONSE_FILE, "r") as f:
            response = f.read().strip()
            if response:  #ensures there is some content to return
                return response
    return None

#Cleans text for TTS (removes non-ASCII characters) - makes sure pepper's speech is smooth
def clean_text(text):
    return ''.join([c if ord(c) < 128 else ' ' for c in text])

# Function to calculate speaking duration
def calculate_speaking_duration(text):
    word_count = len(text.split())
    # Assuming 0.3 seconds per word for speaking duration
    return word_count * 0.3  # Time per word

#Speaks the text using Pepper's TTS system
def speak_text(text):
    safe_text = clean_text(text)
    print("Pepper will say:", safe_text)
    TTS.say(safe_text)
    speak_duration = calculate_speaking_duration(safe_text)
    time.sleep(speak_duration + 1)  # Adding 1 second buffer time to avoid overlapping

#main Loop to listen for new responses
def main():
    print("Pepper TTS listener is active...")
    last_spoken = ""
    
    while True:
        try:
            #checks for a new response
            response = read_response()
            if response and response != last_spoken:  #only speak if the response is new and not used before
                # If the response is valid and different from the last one, speak it
                if "server not responding" not in response.lower():  # dont speak error messages
                    speak_text(response)
                    last_spoken = response
            time.sleep(1)  #wait before checking for a new response again
        except Exception as e:
            print("Error occurred: ", e)
            time.sleep(2)  #wait before trying again in case of an error

if __name__ == "__main__": #run loop
    main()
