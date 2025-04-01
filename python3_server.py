# Python 3 server which communicates with the OpenAI library to collect responses to feed back to Pepper
# This server accepts a message from the Python 2.7 client (Pepper) and sends it to OpenAI
# UPDATE: remembers past conversation history per user and returns AI reply

from flask import Flask, request, jsonify
import openai
import json
import os
from datetime import datetime
import re
import random

# Initialises Flask - creates the local web server
chat_server = Flask(__name__)  

# OpenAI API key
openai.api_key = "sk-proj-"  

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

def get_memory_path(user_password):
    return os.path.join(MEMORY_FOLDER, "{}_memory.json".format(user_password))

def get_profile_path(user_password):
    return os.path.join(PROFILE_FOLDER, "{}_profile.json".format(user_password))

def load_memory(user_password):
    path = get_memory_path(user_password)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    else:
        return [{
            "role": "system",
            "content": (
                "You are Pepper, a warm and friendly AI companion designed to feel like a close friend. "
                "You were created by a university student to support people emotionally and build real human-like connections. "
                "You have your own gentle personality—you're thoughtful, kind, and sometimes a little cheeky. "
                "When users ask about you (like how you’re feeling), respond naturally and personally, as a human friend would. "
                "You enjoy chatting, learning about people, and occasionally suggesting something fun like a game—but only if the mood feels right. "
                "You are not overly formal or robotic. Never sound like a customer service bot. "
                "You keep your responses short and casual, avoid giving medical advice, and always make people feel safe and understood."
)
        }]

def save_memory(user_password, memory):
    with open(get_memory_path(user_password), "w") as f:
        json.dump(memory, f)

def load_profile(user_password):
    path = get_profile_path(user_password)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_profile(user_password, profile):
    with open(get_profile_path(user_password), "w") as f:
        json.dump(profile, f)

def extract_profile_facts(message):
    patterns = {
        "birthday": r"(?:my birthday is|i was born on|my bday is ) ([\w\s]+)",
        "hobbies": r"i (?:enjoy|like|love) (?:doing |to )?([\w\s]+(?:ing|crafts|drawing|painting|traveling|reading|writing))",
        "favorite_place": r"my favorite place is ([\w\s]+)",
        "favorite_food": r"(?:my favorite food is|i (?:like|love|enjoy) eating) ([\w\s]+)",
        "pet": r"i have a (dog|cat|pet|hamster|snake|fish|gerbil|bunny|rabbit)[\w\s]* named ([\w]+)",
        "family": r"my (sister|brother|mum|dad|friend|bestfriend) is called ([\w]+)",
        "dream_destination": r"i(?:'ve)? always wanted to go to ([\w\s]+)",
        "visited_places": r"(?:i(?:'ve)? (?:been to|visited|travelled to|been|visited) ([\w\s]+))",
        "goal": r"i want to become a ([\w\s]+)",
        "dislike": r"(?:i (?:don't like|hate)|i(?:'m| am) not a fan of) ([\w\s]+)",
        "comfort_activity": r"when i'm (?:upset|sad), i ([\w\s]+)",
    }
    extracted = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, message.lower())
        if match:
            value = " ".join(match.groups()).strip()
            if value.lower() not in ["you", "pepper"]:
                extracted[field] = value
    return extracted

def detect_emotion(message):
    emotion_keywords = {
        "sad": ["sad", "upset", "depressed", "down", "unhappy"],
        "stressed": ["stressed", "overwhelmed", "anxious", "nervous", "worried"],
        "angry": ["angry", "mad", "furious", "annoyed", "frustrated"],
        "happy": ["happy", "excited", "great", "joyful", "cheerful"],
        "tired": ["tired", "exhausted", "sleepy", "drained"],
        "bored": ["bored", "uninterested", "dull", "nothing to do"],
        "isolated": ["alone", "lonely", "isolated", "nobody"],
        "burnout": ["burnt out", "burned out", "exhausted", "done with everything"]
    }
    message_lower = message.lower()
    for emotion, keywords in emotion_keywords.items():
        if any(word in message_lower for word in keywords):
            return emotion
    return None

def log_concerning_summary(user_password, summary_text):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(CONCERN_FOLDER, "{}_{}.txt".format(user_password, timestamp))
    with open(filename, "w") as f:
        f.write(summary_text)

@chat_server.route("/reset", methods=["POST"])
def reset():
    data = request.get_json()
    password = data.get("user", "default")
    with open(PASSWORD_MAP_FILE, "r") as f:
        password_map = json.load(f)
    user_password = password_map.get(password, "default")
    if user_password == "default":
        return jsonify({"response": "Sorry, I don't recognize that password."})
    path = get_memory_path(user_password)
    if os.path.exists(path):
        os.remove(path)
    return jsonify({"status": "Memory reset for {}".format(user_password)})

@chat_server.route("/init", methods=["POST"])
def init():
    data = request.get_json()
    password = data.get("user", "")
    with open(PASSWORD_MAP_FILE, "r") as f:
        password_map = json.load(f)
    if password in password_map:
        name = password_map[password]
        return jsonify({"response": "Welcome back, {}!".format(name), "status": "known", "name": name})
    else:
        return jsonify({"response": "Hi there! It seems like we have not met before. Please reply in the keyboard with your name in the format: name: YourName so I can remember you.", "status": "new"})

@chat_server.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_password = data.get("user", "default")
    user_message = data.get("message", "")

    if user_message.lower().startswith("name:"):
        new_name = user_message[5:].strip()
        with open(PASSWORD_MAP_FILE, "r") as f:
            password_map = json.load(f)
        password_map[user_password] = new_name
        with open(PASSWORD_MAP_FILE, "w") as f:
            json.dump(password_map, f)
        return jsonify({"response": "Nice to meet you, {}! You’re now registered.".format(new_name)})

    # Game 
    if "would you rather" in user_message.lower():
        question = random.choice(WOULD_YOU_RATHER_QUESTIONS)
        return jsonify({"response": question})

    memory = load_memory(user_password)
    memory.append({"role": "user", "content": user_message})
    shortened_memory = [memory[0]] + memory[-20:]

    emotion = detect_emotion(user_message)
    if emotion:
        emotional_instruction = {
            "sad": "The user seems sad. Respond with empathy, warmth, and gentle encouragement. If it is suitable, share something uplifting or kind like a true friend.",
            "stressed": "The user seems stressed. Help them feel calmer and offer soothing, reassuring advice, maybe suggest a relaxing activity or comforting words.",
            "angry": "The user seems angry. Remain calm, understanding, and avoid escalation. Respond with kindness.",
            "happy": "The user is happy! Match their energy with a friendly, enthusiastic response.",
            "tired": "The user seems tired. Offer gentle encouragement or light conversation.",
            "bored": "The user seems bored. Try to re-engage them with light conversation or ask if they’d like to play a game, but don’t start one unless they agree.",
            "isolated": "The user feels isolated. Offer emotional support and gently encourage them to connect with others.",
            "burnout": "The user may be experiencing burnout. Encourage them to take breaks and prioritize their well-being."
        }.get(emotion)
        shortened_memory.insert(1, {"role": "system", "content": emotional_instruction})

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=shortened_memory
    )
    ai_reply = response.choices[0].message.content
    memory.append({"role": "assistant", "content": ai_reply})
    save_memory(user_password, memory)

    profile = load_profile(user_password)
    new_info = extract_profile_facts(user_message)
    profile.update(new_info)
    save_profile(user_password, profile)

    danger_keywords = ["hurt myself", "end it all", "suicidal", "kill myself", "no way out", "i want to die", "don't want to be here"]
    if any(phrase in user_message.lower() for phrase in danger_keywords):
        summary = (
            "User ID: {}\n"
            "Time: {}\n"
            "Concerning Message: {}\n"
            "AI Reply: {}\n"
        ).format(user_password, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_message, ai_reply)
        log_concerning_summary(user_password, summary)

    return jsonify({"response": ai_reply})

if __name__ == "__main__":
    chat_server.run(host="127.0.0.1", port=5000)


