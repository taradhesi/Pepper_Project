import openai
import json
import os
import random
from flask import Flask, request, jsonify
from datetime import datetime

# Initialize Flask server
chat_server = Flask(__name__)

# OpenAI API key
openai.api_key = 

# Folder paths
MEMORY_FOLDER = "user_memory"
PROFILE_FOLDER = "user_profiles"
CONCERN_FOLDER = "concerning_logs"

# Ensure folders exist
for folder in [MEMORY_FOLDER, PROFILE_FOLDER, CONCERN_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Path to password-to-user mapping file
PASSWORD_MAP_FILE = "password_map.json"
if not os.path.exists(PASSWORD_MAP_FILE):
    with open(PASSWORD_MAP_FILE, "w") as f:
        json.dump({}, f)

# Sample questions for the "Would You Rather" game
WOULD_YOU_RATHER_QUESTIONS = [
    "Would you rather be able to fly or be invisible?",
    "Would you rather live in the mountains or by the beach?",
    "Would you rather always have to whisper or always have to shout?",
    "Would you rather be super strong or super fast?",
    "Would you rather have no internet or no phone for a month?",
    "Would you rather have the ability to time travel or read minds?"
]

# Emotion detection logic
def detect_emotion(message):
    emotion_keywords = {
        "sad": ["sad", "upset", "depressed", "down", "unhappy"],
        "stressed": ["stressed", "overwhelmed", "anxious", "nervous", "worried"],
        "anxiety": ["anxious", "restless", "nervous", "uneasy"],
        "excited": ["excited", "thrilled", "eager", "enthusiastic"],
        "angry": ["angry", "mad", "furious", "annoyed", "frustrated"],
        "happy": ["happy", "excited", "great", "joyful", "cheerful"],
        "tired": ["tired", "exhausted", "sleepy", "drained"],
        "bored": ["bored", "uninterested", "dull", "nothing to do"],
        "isolated": ["alone", "lonely", "isolated", "nobody"],
        "burnout": ["burnt out", "burned out", "done with everything"]
    }
    message_lower = message.lower()

    for emotion, keywords in emotion_keywords.items():
        if any(word in message_lower for word in keywords):
            return emotion

    return None

# Game question selection based on emotion
def get_game_question(emotion):
    if emotion == "bored":
        return "Would you rather play a game or take a short break?"
    elif emotion == "happy":
        return "Would you rather have a super fun adventure or relax and unwind?"
    elif emotion == "stressed":
        return "Would you rather take a break and relax or keep working on something challenging?"
    elif emotion == "angry":
        return "Would you rather calm down with some music or take a walk?"
    else:
        return random.choice(WOULD_YOU_RATHER_QUESTIONS)  # Default question

def load_memory(user_password):
    path = get_memory_path(user_password)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    else:
        return [{"role": "system", "content": "You are Pepper, a warm and friendly AI companion."}]

def get_memory_path(user_password):
    return os.path.join(MEMORY_FOLDER, f"{user_password}_memory.json")

def save_memory(user_password, memory):
    with open(get_memory_path(user_password), "w") as f:
        json.dump(memory, f)

def load_profile(user_password):
    profile_path = os.path.join(PROFILE_FOLDER, f"{user_password}_profile.json")
    if os.path.exists(profile_path):
        with open(profile_path, "r") as f:
            return json.load(f)
    else:
        return {}

def save_profile(user_password, profile):
    profile_path = os.path.join(PROFILE_FOLDER, f"{user_password}_profile.json")
    with open(profile_path, "w") as f:
        json.dump(profile, f)

def update_user_profile(user_password, key, value):
    profile = load_profile(user_password)
    if key not in profile:
        profile[key] = []
    if isinstance(profile[key], list):
        if value not in profile[key]:
            profile[key].append(value)
    else:
        profile[key] = value
    save_profile(user_password, profile)

# Handle user initialization (registration)
@chat_server.route("/init", methods=["POST"])
def init():
    data = request.get_json()
    password = data.get("user", "")
    if password:
        with open(PASSWORD_MAP_FILE, "r") as f:
            password_map = json.load(f)

        if password in password_map:
            return jsonify({"response": f"Welcome back, {password_map[password]}!", "status": "known", "name": password_map[password]})
        else:
            return jsonify({"response": "Hi there! It seems like we have not met before. Please reply with your name so I can remember you.", "status": "new"})
    return jsonify({"response": "Sorry, I couldn't understand your password. Please try again."})

# Handle conversation messages
@chat_server.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_password = data.get("user", "default")
    user_message = data.get("message", "").strip()

    # Debugging: print what the server hears
    print(f"Whisper heard: {user_message}")  # This will log the exact message received by the server

    # Check if the message is empty or null before proceeding
    if not user_message:
        return jsonify({"response": "I didn't catch that. Can you repeat, please?"})

    # Check for hobbies or preferences (e.g., "I like drawing")
    hobbies_keywords = ["I like", "I enjoy", "My favorite", "I love", "I am passionate about"]
    for phrase in hobbies_keywords:
        if phrase.lower() in user_message.lower():
            hobby = user_message.lower().replace(phrase.lower(), "").strip()
            update_user_profile(user_password, "hobbies", hobby)
            return jsonify({"response": f"Got it! You like {hobby}. I'll remember that!"})

    # Check for birthday input
    if "my birthday is" in user_message.lower():
        birthday = user_message.lower().replace("my birthday is", "").strip()
        update_user_profile(user_password, "birthday", birthday)
        return jsonify({"response": f"Got it! Your birthday is {birthday}. I'll remember that!"})

    # Check for pet info
    if "i have a pet" in user_message.lower():
        pet = user_message.lower().replace("i have a pet", "").strip()
        update_user_profile(user_password, "pet", pet)
        return jsonify({"response": f"Got it! You have a pet, a {pet}. I'll remember that!"})

    # Check for favorite food
    if "my favorite food is" in user_message.lower():
        favorite_food = user_message.lower().replace("my favorite food is", "").strip()
        update_user_profile(user_password, "favorite_food", favorite_food)
        return jsonify({"response": f"Got it! Your favorite food is {favorite_food}. I'll remember that!"})

    # Check for favorite color
    if "my favorite color is" in user_message.lower():
        favorite_color = user_message.lower().replace("my favorite color is", "").strip()
        update_user_profile(user_password, "favorite_color", favorite_color)
        return jsonify({"response": f"Got it! Your favorite color is {favorite_color}. I'll remember that!"})

    # Handle "Let's play a game" and prioritize "Would You Rather"
    if "let's play a game" in user_message.lower():
        memory = load_memory(user_password)

        # Add game prompt directly into memory
        game_prompt = "Let's play 'Would You Rather'!"
        memory.append({"role": "assistant", "content": game_prompt})
        save_memory(user_password, memory)

        # Return the game prompt immediately
        return jsonify({"response": game_prompt})

    # Handle the user's response after "Would You Rather" game is initiated
    if "i would rather" in user_message.lower() or "would rather" in user_message.lower():
        memory = load_memory(user_password)

        # Add the user's response to memory
        memory.append({"role": "user", "content": user_message})
        save_memory(user_password, memory)

        # Return a response from the model
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Correct method for OpenAI API v0.28 or v1.0+
                messages=memory
            )
            ai_reply = response['choices'][0]['message']['content']

            # Ensure the response is valid and non-empty
            if ai_reply:
                memory.append({"role": "assistant", "content": ai_reply})
                save_memory(user_password, memory)
                return jsonify({"response": ai_reply})
            else:
                return jsonify({"response": "Sorry, I didn't catch that. Could you repeat?"})

        except Exception as e:
            print(f"Error during OpenAI request: {e}")
            return jsonify({"response": "I'm having trouble connecting to my brain. Please try again later."})

    # Regular conversation handling (only when not playing a game)
    memory = load_memory(user_password)
    memory.append({"role": "user", "content": user_message})
    shortened_memory = [memory[0]] + memory[-20:]

    emotion = detect_emotion(user_message)
    if emotion:
        emotional_instruction = {
            "sad": "The user seems sad...",
            "stressed": "The user seems stressed...",
            # Add more emotional states as needed
        }.get(emotion)
        shortened_memory.insert(1, {"role": "system", "content": emotional_instruction})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Ensure the model is available
            messages=shortened_memory
        )
        ai_reply = response['choices'][0]['message']['content']

        # Ensure the response is valid and non-empty
        if ai_reply:
            memory.append({"role": "assistant", "content": ai_reply})
            save_memory(user_password, memory)
            return jsonify({"response": ai_reply})
        else:
            return jsonify({"response": "Sorry, I didn't catch that. Could you repeat?"})

    except Exception as e:
        print(f"Error during OpenAI request: {e}")
        return jsonify({"response": "I'm having trouble connecting to my brain. Please try again later."})


if __name__ == "__main__":
    chat_server.run(host="127.0.0.1", port=5000)
