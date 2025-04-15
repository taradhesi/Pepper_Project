import time
import os
from naoqi import ALProxy

PEPPER_IP = "192.168.0.13"  # Change this to your Pepper's IP address
TTS = ALProxy("ALTextToSpeech", PEPPER_IP, 9559)
RESPONSE_FILE = "latest_response.txt"  # Text file updated by Whisper script

# Read the file containing the message for Pepper to speak
def read_response():
    if os.path.exists(RESPONSE_FILE):
        with open(RESPONSE_FILE, "r") as f:
            response = f.read().strip()
            if response:  # Ensure there is some content to return
                return response
    return None

# Clean text for TTS (remove non-ASCII characters)
def clean_text(text):
    return ''.join([c if ord(c) < 128 else ' ' for c in text])

# Function to calculate speaking duration
def calculate_speaking_duration(text):
    word_count = len(text.split())
    # Assuming 0.3 seconds per word for speaking duration
    return word_count * 0.3  # Time per word is adjustable

# Speak the text using Pepper's TTS system
def speak_text(text):
    safe_text = clean_text(text)
    print("Pepper will say:", safe_text)
    TTS.say(safe_text)
    speak_duration = calculate_speaking_duration(safe_text)
    time.sleep(speak_duration + 1)  # Adding 1 second buffer time

# MAIN Loop to continuously listen for new responses
def main():
    print("Pepper TTS listener is active...")
    last_spoken = ""
    
    while True:
        try:
            # Check for a new response
            response = read_response()
            if response and response != last_spoken:  # Only speak if the response is new
                # If the response is valid and different from the last one, speak it
                if "server not responding" not in response.lower():  # Avoid speaking error messages
                    speak_text(response)
                    last_spoken = response
            time.sleep(1)  # Wait before checking for a new response again
        except Exception as e:
            print("Error occurred: ", e)
            time.sleep(2)  # Wait before trying again in case of an error

if __name__ == "__main__":
    main()
