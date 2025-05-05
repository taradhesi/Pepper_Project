# Pepper_Project

The files to be run simultaneously are :

Python3_server.py, pepper2.7_tts_test.py and whisperapiscript.py

Python3_server: Contains flask server, provides OpenAI reponses and password handling, all emotional prompts and game theory etc
pepper2.7_tts_test: Pepper script for TTS module with NAOqi library - responses from pepper 
whisperapi_script: TTS script for laptop microphone to transcibe speech and send to the python 3 server for the AI responses.

There are two environments to handle python 2.7 and python 3.14:
-whisper_env(python 3): must be activated with conda to run the python 3 server and whisper api scripts
"conda activate whisper_env
python python3_server.py"

"conda activate whisper_env
python whisperapiscript.py"
-ensure the laptop ip is correct otherwise will not work

-pepper_env(python 2.7)
"conda activate pepper_env
python pepper2.7_tts_test.py"
-ensure the laptop ip and pepper ip is correct otherwise will not work
-ensure dual wifi usb is in and connected to pepper local network and internet for AI library

use password "sunshine" for tests
