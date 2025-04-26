import openai #chatGPT
import json 
import os
import random #selects random game q's
from flask import Flask, request, jsonify #communication server
from datetime import datetime #for date and timestamps
import bcrypt #for hashing passwords
import time 


# Initialise Flask server
chat_server = Flask(__name__)

# OpenAI API key
openai.api_key = "

# Folder paths
MEMORY_FOLDER = "user_memory"
PROFILE_FOLDER = "user_profiles"
CONCERN_FOLDER = "concerning_logs"

#Ensures folders exist
for folder in [MEMORY_FOLDER, PROFILE_FOLDER, CONCERN_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

#Path to password-to-user mapping file
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

 #List of possible mental health conditions to check for
MENTAL_HEALTH_CONDITIONS = [
    "depression", "anxiety", "stress", "bipolar", "schizophrenia", "ptsd", 
    "ocd", "phobia", "panic disorder", "eating disorder", "addiction"
]


# Function to log response times to a file for analysis
#def log_response_time(user_password, response_time, word_length):
     # Debug print to check the function is being called
    #print("Logging response time and word length...", flush=True)
     #Log the response time to a file (you can customize this as needed)
    #log_entry = {
     #   "user_password": user_password,
      #  "timestamp": datetime.now().isoformat(),
       # "response_time": response_time , # in seconds
        #"word_length": word_length  # number of words in the response
    #}

     # Log file path
    #log_file = "response_times_log.json"

    # If the log file exists, append to it, otherwise create a new one
    #if os.path.exists(log_file):
     #   print("Log file exists. Appending to the file...",)
      #  with open(log_file, "r") as f:
       #     logs = json.load(f)
        #logs.append(log_entry)
        #print("Log file does not exist. Creating new file...", )
    #else:
     #   logs = [log_entry]

    #try:
     #   with open(log_file, "w") as f:
      #      json.dump(logs, f, indent=4)
       # print(f"Log saved successfully to {log_file}",)
    #except Exception as e:
     #   print(f"Error saving log: {e}", )


    
#function to get the users name
def get_user_name():
    # Prompt the user to speak their name
    print("Please say your name.")
    user_name = get_speech_input()  # using whisper API
    
    if not user_name:
        # keyboard fallback
        print("No voice input detected. Please type your name:")
        user_name = input("Enter your name: ").strip()

    return user_name


# Emotion detection logic (list of emotions were generated with AI - chatGPT)
def detect_emotion(message):
    emotion_keywords = {
       "sad": ["sad", "upset", "depressed", "down", "unhappy", "feeling blue", "low mood", "grief", "sorrow", "heartbroken", "melancholy", "mournful"],
        "stressed": ["stressed", "overwhelmed", "anxious", "nervous", "worried", "tense", "pressure", "burnout", "stressed out", "frazzled"],
        "anxiety": ["anxious", "restless", "uneasy", "nervous", "scared", "fearful", "panicking", "worry", "fidgety", "on edge"],
        "excited": ["excited", "thrilled", "eager", "enthusiastic", "pumped", "ecstatic", "joyful", "delighted", "cheerful", "hyper"],
        "angry": ["angry", "mad", "furious", "annoyed", "frustrated", "irritated", "enraged", "livid", "outraged", "upset"],
        "happy": ["happy", "joyful", "content", "cheerful", "excited", "pleased", "satisfied", "grateful", "smiling", "optimistic"],
        "tired": ["tired", "exhausted", "sleepy", "drained", "fatigued", "burnt out", "low energy", "weary", "drowsy", "worn out"],
        "bored": ["bored", "uninterested", "dull", "disinterested", "nothing to do", "apathetic", "indifferent", "unmotivated"],
        "isolated": ["alone", "lonely", "isolated", "nobody understands", "no one to talk to", "feeling disconnected", "feeling left out"],
        "burnout": ["burnt out", "worn out", "overworked", "out of energy", "mentally drained", "unmotivated", "unproductive", "stressed beyond capacity"],
        "guilty": ["guilty", "ashamed", "regretful", "remorseful", "blaming myself", "feeling bad", "feeling sorry", "disappointed with myself"],
        "confused": ["confused", "uncertain", "lost", "perplexed", "puzzled", "disoriented", "not sure", "clueless", "unsure"],
        "hopeful": ["hopeful", "optimistic", "looking forward", "positive", "expecting good things", "anticipating", "believing in the future"],
        "embarrassed": ["embarrassed", "ashamed", "self-conscious", "awkward", "feeling exposed", "red-faced", "cringey", "uncomfortable"],
        "jealous": ["jealous", "envious", "coveting", "resentful", "wanting what others have", "insecure", "feeling left out", "feeling inferior"],
        "surprised": ["surprised", "shocked", "amazed", "astonished", "startled", "dumbfounded", "baffled", "taken aback", "unexpected"],
        "grateful": ["grateful", "thankful", "appreciative", "indebted", "honored", "thank you", "appreciation", "grateful for", "blessed"],
        "relieved": ["relieved", "calm", "at peace", "unburdened", "free", "less stressed", "relaxing", "settled", "comforted", "peaceful"],
        "disappointed": ["disappointed", "let down", "unhappy", "dissatisfied", "unfulfilled", "disheartened", "disillusioned", "sad about", "regretful"],
        "proud": ["proud", "accomplished", "satisfied with myself", "feeling great", "feeling good about", "honored", "successful", "achievement"],
    }
    message_lower = message.lower()

    for emotion, keywords in emotion_keywords.items():
        if any(word in message_lower for word in keywords):
            return emotion

    return None

#fucntion
def check_mental_health_condition(user_message):

   #Checks if the user mentions any known mental health condition in their message.
    
    user_message_lower = user_message.lower()

    for condition in MENTAL_HEALTH_CONDITIONS:
        if condition in user_message_lower:
            return condition  #Return the condition if found
    
    return None  #if no condition is mentioned

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
        return random.choice(WOULD_YOU_RATHER_QUESTIONS)  # Default questions

#function to load users memory
def load_memory(user_password):
    path = get_memory_path(user_password)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    else:
        #system prompt if no memory exists
        return [{"role": "system", "content": "You are Pepper, a warm and friendly AI companion designed to help those suffering from mental health struggles. "
            "Keep your responses short and concise with no more than 20-30 words. "
            "Avoid providing medical diagnoses. Always respond in a human-like, empathetic, and supportive manner."
            "Your role is to offer encouragement, listen, and provide helpful suggestions, not to diagnose or treat medical conditions."
            "Ensure you maintain a compassionate and understanding tone."}]
#function for memory
def get_memory_path(user_password):
    return os.path.join(MEMORY_FOLDER, f"{user_password}_memory.json")
#fucntion for 
def save_memory(user_password, memory):
    with open(get_memory_path(user_password), "w") as f:
        json.dump(memory, f)

#functions to load and save user profiles
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

#updates with new profile chnages
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



# Handles user registration with passwords
@chat_server.route("/init", methods=["POST"])
def init():
    data = request.get_json()
    password = data.get("user", "")
    if password:
        with open(PASSWORD_MAP_FILE, "r") as f:
            password_map = json.load(f)

        if password in password_map:
            # If the password exists, check the hashed password
            stored_hash = password_map[password]["hash"]
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                # If the password is correct, return a response
                return jsonify({"response": f"Welcome back, {password_map[password]['name']}!", "status": "known", "name": password_map[password]['name']})
            else:
                return jsonify({"response": "Error: Incorrect password. Please try again.", "status": "error"})
        else:
            # If the password is new, hash it and store it - doesnt work with pepper2.7_Tts_test (admin only)
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            #Prompts the user for their name
            user_name = get_user_name()

            #Stores the new password and name in the password map
            password_map[password] = {"hash": hashed_password, "name": user_name}

            #saves the updated password map to the file
            with open(PASSWORD_MAP_FILE, "w") as f:
                json.dump(password_map, f)

            #Stores the name in the user's profile
            save_profile(password, {"name": user_name})

            return jsonify({"response": f"Hi {user_name}! It seems like we have not met before. I'll remember you from now on.", "status": "new"})

    return jsonify({"response": "Sorry, I couldn't understand your password. Please try again."})


#Handles conversation messages
@chat_server.route("/chat", methods=["POST"])
def chat():

    #log_response_time("test_user", 0.45, 100)  # Just for testing uncomment when done

    data = request.get_json()
    user_password = data.get("user", "default")
    user_message = data.get("message", "").strip()

    # Debugging- prints what the server hears
    print(f"Whisper heard: {user_message}")  

    if user_password:  
        #Verifies the password using bcrypt
        with open(PASSWORD_MAP_FILE, "r") as f:
            password_map = json.load(f)

        # If password exists in the password_map, check the hashed password
        if user_password in password_map:
            stored_hash = password_map[user_password]["hash"]
            if bcrypt.checkpw(user_password.encode('utf-8'), stored_hash.encode('utf-8')):
                print("Password is correct.")
            else:
                return jsonify({"response": "Incorrect password."})

    #Checks if the message is empty/null before proceeding
    if not user_message:
        return jsonify({"response": "I didn't catch that. Can you repeat, please?"})
    
        
    # Start timing before sending the request to OpenAI API FOR RESPONSE LOGGING
    #start_time = time.time()
    
     #Checks for mental health conditions and update the profile if needed
    mental_health_keywords = ["depression", "anxiety", "stress", "burnout", "sad", "worried", "bipolar", "schizophrenia", "ptsd", 
    "ocd", "phobia", "panic disorder", "eating disorder", "addiction"]
    
    for condition in mental_health_keywords:
        if condition in user_message.lower():
            # Update the profile with the detected mental health condition
            update_user_profile(user_password, "mental_health_conditions", condition)

            break
  


    #Checks for hobbies 
    hobbies_keywords = ["I like", "I enjoy", "My favorite", "I love", "I am passionate about"]
    for phrase in hobbies_keywords:
        if phrase.lower() in user_message.lower():
            hobby = user_message.lower().replace(phrase.lower(), "").strip()
            update_user_profile(user_password, "hobbies", hobby)

            break
    

    #Checks for birthday input
    if "my birthday is" in user_message.lower():
        birthday = user_message.lower().replace("my birthday is", "").strip()
        update_user_profile(user_password, "birthday", birthday)
        

    #Checks for pet info
    if "i have a pet" in user_message.lower():
        pet = user_message.lower().replace("i have a pet", "").strip()
        update_user_profile(user_password, "pet", pet)
        

    #Checks for favorite food
    if "my favorite food is" in user_message.lower():
        favorite_food = user_message.lower().replace("my favorite food is", "").strip()
        update_user_profile(user_password, "favorite_food", favorite_food)
        

    #Checks for favorite color
    if "my favorite color is" in user_message.lower():
        favorite_color = user_message.lower().replace("my favorite color is", "").strip()
        update_user_profile(user_password, "favorite_color", favorite_color)
        

    #Handles "Let's play a game" and prioritise "Would You Rather"
    if "let's play a game" in user_message.lower():
        memory = load_memory(user_password)

        #adds game prompt directly into memory
        game_prompt = "Let's play 'Would You Rather'!"
        memory.append({"role": "assistant", "content": game_prompt})
        save_memory(user_password, memory)

        #reurns the game prompt immediately
        return jsonify({"response": game_prompt})

    #handles the users response after "Would You Rather" game is initiated
    if "i would rather" in user_message.lower() or "would rather" in user_message.lower():
        memory = load_memory(user_password)

        #Adds the user's response to memory for future use
        memory.append({"role": "user", "content": user_message})
        save_memory(user_password, memory)

        #Returns a response from the chatGPT
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  
                messages=memory
            )
            ai_reply = response['choices'][0]['message']['content']

            #ensures the response is valid and non empty
            if ai_reply:
                memory.append({"role": "assistant", "content": ai_reply})
                save_memory(user_password, memory)
                return jsonify({"response": ai_reply})
            else:
                return jsonify({"response": "Sorry, I didn't catch that. Could you repeat?"})

        except Exception as e:
            print(f"Error during OpenAI request: {e}")
            return jsonify({"response": "I'm having trouble connecting to my brain. Please try again later."}) #debug and error handling

    # Regular conversation handling (only when not playing a game)
    memory = load_memory(user_password)
    memory.append({"role": "user", "content": user_message})
    shortened_memory = [memory[0]] + memory[-20:] #for token efficiency

    emotion = detect_emotion(user_message)
    if emotion:
        emotional_instruction = {
        "sad": "The user seems sad...", #emotions generated via AI
        "stressed": "The user seems stressed...",
        "anxiety": "The user seems anxious or worried...",
        "excited": "The user seems excited or thrilled...",
        "angry": "The user seems angry or frustrated...",
        "happy": "The user seems happy and cheerful...",
        "tired": "The user seems tired or exhausted...",
        "bored": "The user seems bored or uninterested...",
        "isolated": "The user seems lonely or isolated...",
        "burnout": "The user seems burnt out or overworked...",
        "guilty": "The user seems guilty or remorseful...",
        "confused": "The user seems confused or uncertain...",
        "hopeful": "The user seems hopeful or optimistic...",
        "embarrassed": "The user seems embarrassed or awkward...",
        "jealous": "The user seems jealous or envious...",
        "surprised": "The user seems surprised or astonished...",
        "grateful": "The user seems grateful or appreciative...",
        "relieved": "The user seems relieved or at peace...",
        "disappointed": "The user seems disappointed or let down...",
        "proud": "The user seems proud or accomplished..."
            
            
        }.get(emotion)
        shortened_memory = [{"role": "system", "content": emotional_instruction}] + memory[-20:]  # Keeps memory flow

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  #ensures the model is available
            messages=shortened_memory
        )

         # End timing after receiving the response
        #end_time = time.time()
#
        # Calculate the response time (in seconds)
        #response_time = end_time - start_time

        # Get the AI's response and calculate the word length (word count)
        #ai_reply = response['choices'][0]['message']['content']
        #word_length = len(ai_reply.split())  # Count the number of words in the response

       # log_response_time(user_password, response_time, word_length)  # Log the response time
#prompt
        ai_reply = response['choices'][0]['message']['content']

        #Ensures the response is valid and non empty
        if ai_reply:
            memory.append({"role": "assistant", "content": ai_reply})
            save_memory(user_password, memory)
            return jsonify({"response": ai_reply})
        else:
            return jsonify({"response": "Sorry, I didn't catch that. Could you repeat?"})

    except Exception as e:
        print(f"Error during OpenAI request: {e}")
        return jsonify({"response": "I'm having trouble connecting to my brain. Please try again later."}) #debug


if __name__ == "__main__":
    chat_server.run(host="127.0.0.1", port=5000)
