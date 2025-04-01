# Python 2.7 client file for Pepper to be run on the same laptop as the Python 3 server
# Lets Pepper send messages to the Python 3 server and get replies from OpenAI
# Sends requests to the Python 3 Flask server using HTTP

import requests

# Sends a message and user password to the Python 3 server
def chat_with_gpt(user_password, user_input):
    SERVER_IP = "127.0.0.1"  # Change to laptop's IP when using Pepper
    PORT = 5000

    # Sends the user's message to the /chat endpoint using POST
    try:
        response = requests.post(
            "http://{}:{}/chat".format(SERVER_IP, PORT),
            json={"user": user_password, "message": user_input}
        )
        if response.status_code == 200:  # If server responds successfully, return the AI's message
            return response.json()["response"]
        else:
            return "Error: AI server not responding."
    except Exception as e:
        return "Error: " + str(e)

# asks the server to check if user is known or new
def init_user(user_password):
    SERVER_IP = "127.0.0.1"
    PORT = 5000
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

# Ask for the user's password (will be replaced with speech later)
user_password = raw_input("Welcome! Please enter your password (or a new one to register): ")

# Immediately show welcome or registration message
init_message = init_user(user_password)
print("Pepper: " + init_message.encode('utf-8'))

# Loop for chatting to OpenAI
while True:
    user_input = raw_input("You: ")  # Python 2.7 input function
    response = chat_with_gpt(user_password, user_input)
    print("Pepper: " + response.encode('utf-8'))