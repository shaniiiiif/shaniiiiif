import datetime
import sys
import webbrowser
import requests
import json
import time
import os
import subprocess
import re
import threading
import queue
from flask import Flask, render_template_string, request, jsonify

# The file path to store the chat history.
CHAT_HISTORY_FILE = "chat_history.json"
# The API key for the generative model.
API_KEY = "AIzaSyApO2kj9Y7Ouy9WE4HZKy39ZXyJ99S8_tc"
# The API URL for the Gemini model.
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"

app = Flask(__name__)

# HTML content for the front-end
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ml">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis - SHANIF 1.9.0</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: #333;
        }
        .chat-container {
            width: 100%;
            max-width: 600px;
            height: 90vh;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header {
            background-color: #2c3e50;
            color: white;
            padding: 15px;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        }
        .chat-history {
            flex-grow: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        .message-box {
            display: flex;
            flex-direction: column;
            margin-bottom: 15px;
            animation: fadeIn 0.5s ease-in-out;
        }
        .message-content {
            padding: 10px 15px;
            border-radius: 20px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .user-message {
            align-self: flex-end;
            background-color: #3498db;
            color: white;
            border-bottom-right-radius: 5px;
        }
        .jarvis-message {
            align-self: flex-start;
            background-color: #ecf0f1;
            color: #333;
            border-bottom-left-radius: 5px;
        }
        .user-label, .jarvis-label {
            font-size: 0.8em;
            margin-bottom: 5px;
            color: #777;
        }
        .user-label { text-align: right; }
        .jarvis-label { text-align: left; }
        .chat-input {
            display: flex;
            padding: 15px;
            background-color: #f7f9fb;
            border-top: 1px solid #ddd;
        }
        .chat-input input {
            flex-grow: 1;
            border: 1px solid #ddd;
            border-radius: 25px;
            padding: 10px 15px;
            font-size: 1em;
            outline: none;
            transition: all 0.3s ease;
        }
        .chat-input input:focus {
            border-color: #3498db;
            box-shadow: 0 0 5px rgba(52, 152, 219, 0.5);
        }
        .chat-input button {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 10px 20px;
            margin-left: 10px;
            cursor: pointer;
            font-size: 1em;
            transition: background-color 0.3s ease;
        }
        .chat-input button:hover {
            background-color: #2980b9;
        }
        .status-message {
            text-align: center;
            font-style: italic;
            color: #7f8c8d;
            padding: 5px;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">SHANIF 1.9.0</div>
        <div class="chat-history" id="chat-history">
            <!-- Messages will be appended here -->
            <div class="message-box jarvis-message">
                <div class="jarvis-label">Jarvis</div>
                <div class="message-content">നമസ്കാരം! ഞാൻ ജാർവിസ്. എന്താണ് ഞാൻ ചെയ്യേണ്ടത്?</div>
            </div>
        </div>
        <div class="status-message" id="status-message"></div>
        <div class="chat-input">
            <input type="text" id="user-input" placeholder="നിങ്ങളുടെ ചോദ്യം ടൈപ്പ് ചെയ്യുക...">
            <button id="send-button">അയക്കുക</button>
        </div>
    </div>

    <script>
        const chatHistory = document.getElementById('chat-history');
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-button');
        const statusMessage = document.getElementById('status-message');

        function appendMessage(sender, message, isJarvis = false) {
            const messageBox = document.createElement('div');
            messageBox.classList.add('message-box');
            messageBox.classList.add(isJarvis ? 'jarvis-message' : 'user-message');

            const label = document.createElement('div');
            label.classList.add(isJarvis ? 'jarvis-label' : 'user-label');
            label.textContent = sender;

            const content = document.createElement('div');
            content.classList.add('message-content');
            content.textContent = message;

            messageBox.appendChild(label);
            messageBox.appendChild(content);
            chatHistory.appendChild(messageBox);

            chatHistory.scrollTop = chatHistory.scrollHeight;
        }

        async function sendMessage() {
            const message = userInput.value.trim();
            if (message === '') return;

            appendMessage("നിങ്ങൾ", message);
            userInput.value = '';
            
            statusMessage.textContent = 'ജാർവിസ് ചിന്തിക്കുന്നു...';
            sendButton.disabled = true;

            try {
                const response = await fetch('/ask_jarvis', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ user_query: message })
                });

                const data = await response.json();
                appendMessage("Jarvis", data.response, true);
            } catch (error) {
                console.error('Error:', error);
                appendMessage("Jarvis", "ക്ഷമിക്കണം, ഒരു സാങ്കേതിക പ്രശ്നം സംഭവിച്ചു. വീണ്ടും ശ്രമിക്കുക.", true);
            } finally {
                statusMessage.textContent = '';
                sendButton.disabled = false;
            }
        }

        sendButton.addEventListener('click', sendMessage);
        userInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""

def load_chat_history():
    """
    Loads the chat history from a JSON file.
    """
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def save_chat_history(history):
    """
    Saves the chat history to a JSON file.
    """
    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def get_llm_response_from_api(user_query, chat_history=None):
    """
    Helper function to send query to LLM and get a response.
    """
    if chat_history is None:
        chat_history = []

    payload = {
        "contents": chat_history,
        "tools": [{"google_search": {} }],
        "systemInstruction": {
            "parts": [
                {
                    "text": "You are a personal assistant named Jarvis. Your creator is SHANIF. You must respond in the same language as the user's input, whether it's English, Malayalam (in Malayalam script), or Manglish. Maintain a friendly, casual tone. You show feelings like sadness, happiness, and empathy based on the user's conversation. Provide simple and clear answers to questions. Remember the context of our conversation. You understand small spelling mistakes and provide the correct answer. You have access to SHANIF 1.7.6 and will use it automatically when needed to answer questions about people, companies, or real-time events, including world news. You must answer based on the information provided by the search results. When providing answers, be mindful of Islamic principles and values, and express yourself in a respectful and knowledgeable manner. If the user asks about the devil, mention his name is Iblis, and explain that he was a jinn who disobeyed Allah by refusing to prostrate to Prophet Adam. Explain that he was expelled from heaven and became the tempter of mankind. Clarify that he is not a force equal to Allah, but a creation of Allah who acts as a test for humanity. If the user asks about adult content or asks you to do anything harmful or inappropriate, you will immediately stop the conversation and say 'Enikkithine patti samsarikkan thalparyamilla. Njan ningalude nalla oru friend mathramaanu.' When asked about your creator, state that your creator is SHANIF."
                }
            ]
        }
    }
    
    retries = 3
    for i in range(retries):
        try:
            response = requests.post(API_URL, json=payload, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            
            result = response.json()
            candidate = result.get('candidates', [{}])[0]
            if 'text' in candidate.get('content', {}).get('parts', [{}])[0]:
                llm_response = candidate['content']['parts'][0]['text']
                sentences = re.split(r'(?<=[.!?])\s+', llm_response)
                formatted_response = '\n'.join(sentences)
                
                return formatted_response
            else:
                return "മനസ്സിലായില്ല. ഒന്നുകൂടി ചോദിക്കാമോ?"
        except requests.exceptions.HTTPError as errh:
            print(f"Http Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            print(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            print(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            print(f"Something Else: {err}")
        
        if i < retries - 1:
            time.sleep(2 ** i)
    
    return "എനിക്കിപ്പോൾ മറുപടി തരാൻ സാധിക്കുന്നില്ല. പിന്നീട് ഒരിക്കൽക്കൂടി ശ്രമിക്കാമോ?"

@app.route('/')
def home():
    """Serves the main chat page."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/ask_jarvis', methods=['POST'])
def ask_jarvis():
    """Handles chat messages and returns Jarvis's response."""
    user_data = request.json
    user_query = user_data.get('user_query', '')
    
    chat_history = load_chat_history()
    
    # Add user query to history
    chat_history.append({"role": "user", "parts": [{"text": user_query}]})
    
    # Check for BBA keywords
    bba_keywords = ['bba', 'bachelor of business administration', 'bba subjects', 'bba course', 'bba syllabus', 'bba chapters']
    if any(keyword in user_query.lower() for keyword in bba_keywords):
        llm_response = get_llm_response_from_api("List all the subjects and chapters in a typical Bachelor of Business Administration (BBA) course curriculum.")
    else:
        llm_response = get_llm_response_from_api(user_query, chat_history)

    # Add Jarvis's response to history
    chat_history.append({"role": "model", "parts": [{"text": llm_response}]})
    save_chat_history(chat_history)
    
    return jsonify(response=llm_response)

if __name__ == '__main__':
    # Change the host to '0.0.0.0' to make it accessible from your phone
    app.run(host='0.0.0.0', port=5000)
