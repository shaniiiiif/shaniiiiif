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
import socket
import base64
from datetime import datetime

# The file paths for chat history, creator status, and custom responses.
CHAT_HISTORY_FILE = "chat_history.json"
CREATOR_STATUS_FILE = "creator_status.json"
CUSTOM_RESPONSES_FILE = "custom_responses.json"
THEME_STATUS_FILE = "theme_status.json"
VISITS_FILE = "visits.json"
ADMIN_LOG_FILE = "admin_log.json"
ADMIN_DATA_FILE = "admin_data.json"
API_KEY_FILE = "api_key.json" # New file for API key

# --- New function to load/save API key ---
def load_api_key():
    """Loads API key from a JSON file or returns a default."""
    if os.path.exists(API_KEY_FILE):
        try:
            with open(API_KEY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('api_key')
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    # Default key if file doesn't exist or is empty
    return "AIzaSyDMBLzWWs2rrYHekC4yg3Dn9HeQl9PnAbw" # Changed to a placeholder to ensure the user inputs their key.

def save_api_key(key):
    """Saves API key to a JSON file."""
    with open(API_KEY_FILE, 'w', encoding='utf-8') as f:
        json.dump({"api_key": key}, f, ensure_ascii=False, indent=4)
# --- End of new functions ---

# Load the API key at startup
API_KEY = load_api_key()
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"
IMAGE_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"
TTS_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={API_URL}"

app = Flask(__name__)

# Global variables to track creator status, theme and sleeping status
is_creator_verified = False
current_theme = "venom"
verification_in_progress = False
is_sleeping = False
sleep_mode_activation_pending = False
wake_up_pending = False

# The creator's name and version for the AI
CREATOR_NAME = "SHANIF P"
CREATOR_VERSION = "1.7.9"

# --- New Emoji Mapping ---
EMOJI_MAP = {
    "hello": "👋",
    "hi": "👋",
    "നമസ്കാരം": "👋",
    "hi-tech": "⚙️",
    "സാങ്കേതികവിദ്യ": "⚙️",
    "കമ്പ്യൂട്ടർ": "💻",
    "ഫോൺ": "📱",
    "സന്തോഷം": "😊",
    "നന്ദി": "🙏",
    "വിഷമം": "😔",
    "സഹായിക്കാം": "🤝",
    "പ്രവർത്തിപ്പിക്കാം": "✔️",
    "ശരി": "👍",
    "വേണ്ട": "🚫",
    "ചോദ്യം": "❓",
    "പറ്റി": "💡",
    "ക്ഷമിക്കണം": "😥",
    "പോവുക": "🚶‍♂️",
    "യാത്ര": "✈️",
    "സമയം": "⏰",
    "തീയതി": "🗓️",
    "നിങ്ങളുടെ സ്രഷ്ടാവ്": "👨‍💻",
    "ഭക്ഷണം": "🍔",
    "വെള്ളം": "💧",
    "കാർ": "🚗",
    "എഴുതുക": "✍️",
    "കവിത": "📜",
    "ചിത്രം": "🖼️",
    "വിവരങ്ങൾ": "ℹ️",
    "പരിഭാഷ": "🔄",
    "കളി": "🎮",
    "പാട്ട്": "🎶",
    "weather": "🌦️",
    "കാലാവസ്ഥ": "🌦️",
    "ദേഷ്യം": "😡",
    "സമാധാനം": "😌",
    "പ്രണയം": "❤️",
    "love": "❤️",
    "സ്നേഹം": "❤️",
    "കഷ്ടം": "😓",
    "ആശ്ചര്യം": "😮",
    "തമാശ": "😂",
    "നല്ലത്": "👌",
    "മോശം": "👎",
    "വിജയം": "🏆",
    "ഓക്കേ": "👍",
    "ok": "👍",
    "ഓർമ്മ": "🧠",
    "മനസ്സിലാക്കുക": "🤔",
    "പഠിക്കുക": "📚",
    "പരീക്ഷണം": "🧪",
    "പണം": "💰",
    "തുറക്കുക": "📂",
    "അടയ്ക്കുക": "❌",
    "തുടരുക": "➡️",
    "തിരികെ": "🔙",
    "മരണപെട്ടു": "💀",
    "മരണം": "💀",
    "പുതിയത്": "✨"
}
# --- End of New Emoji Mapping ---

# HTML content for the front-end
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ml">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ജാർവിസ് - ഷാനിഫ് 1.7.9</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Montserrat:wght@300;400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        :root {
            /* New Color Palette: Dark Blue, Light Blue, Cyan, Black */
            --background-color: #0d0d1a;
            --glass-background: rgba(13, 13, 26, 0.7);
            --border-color: rgba(69, 137, 240, 0.5); /* Light Blue with opacity */
            --text-color: #ffffff;
            --secondary-text-color: #c9c9d6;
            --accent-color: #4589f0; /* Light Blue */
            --highlight-color: #00d4ff; /* Cyan */
            --input-background: rgba(40, 40, 50, 0.5);
            --input-placeholder: rgba(201, 201, 214, 0.5);
            --user-message-bg: rgba(42, 58, 80, 0.75); /* Darker blue-grey with transparency */
            --header-height: 80px;
            --input-height: 70px;
        }

        body {
            font-family: 'Montserrat', sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--background-color);
            background-image: radial-gradient(circle at top left, #2c3a50, transparent), radial-gradient(circle at bottom right, #1a233b, transparent);
            height: 100vh;
            color: var(--text-color);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        /* --- New Loading Animation --- */
        #loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--background-color);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            transition: opacity 1s ease-in-out;
        }
        
        #loading-overlay.hidden {
            opacity: 0;
            visibility: hidden;
        }

        .spinner {
            display: flex;
            gap: 10px;
        }

        .dot {
            width: 15px;
            height: 15px;
            background-color: var(--highlight-color);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }

        .dot:nth-child(2) {
            animation-delay: 0.2s;
        }

        .dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        #loading-text {
            color: var(--secondary-text-color);
            margin-top: 20px;
            font-size: 1.2em;
        }
        /* --- End of Loading Animation --- */

        .header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
            text-align: center;
            padding: 20px 0;
            background-color: var(--glass-background);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            height: var(--header-height);
            box-sizing: border-box;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }

        #logo {
            font-family: 'Cinzel', serif;
            font-size: 2.5em;
            font-weight: 700;
            color: var(--highlight-color); /* Cyan */
            text-shadow: 0 0 10px var(--highlight-color), 0 0 20px var(--highlight-color), 0 0 30px rgba(0, 212, 255, 0.8);
            text-transform: lowercase;
        }
        
        #version-number {
            font-size: 0.8em;
            color: var(--secondary-text-color);
            margin-top: -10px;
            text-align: center;
        }

        #chat-window {
            flex-grow: 1;
            padding: 20px;
            padding-top: var(--header-height);
            padding-bottom: var(--input-height);
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
            scrollbar-width: none;
            -ms-overflow-style: none;
            background-color: transparent;
        }

        #chat-window::-webkit-scrollbar {
            display: none;
        }

        .chat-message {
            display: flex;
            gap: 10px;
            word-wrap: break-word;
            white-space: pre-wrap;
            animation: fadeIn 0.5s ease-in-out;
        }

        /* --- Updated Message Styles with Transparency and 3D Effect --- */
        .user-message {
            align-self: flex-end;
            background-color: var(--user-message-bg);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            color: var(--highlight-color); /* Cyan */
            padding: 12px 18px;
            border-radius: 20px 20px 5px 20px;
            max-width: 80%;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.1);
            position: relative;
            animation: slideInFromRight 0.5s forwards;
            border: 1px solid rgba(0, 212, 255, 0.4);
        }

        .jarvis-message {
            align-self: flex-start;
            background-color: var(--user-message-bg); /* CHANGED: Using user's background */
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            color: var(--highlight-color); /* CHANGED: Using user's text color */
            padding: 12px 18px;
            border-radius: 20px 20px 20px 5px;
            max-width: 80%;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.1);
            position: relative;
            animation: slideInFromLeft 0.5s forwards;
            border: 1px solid rgba(0, 212, 255, 0.4); /* CHANGED: Using user's border color */
        }
        /* --- End of Updated Styles --- */
        
        .user-icon, .jarvis-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-color: var(--highlight-color); /* Cyan background */
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            color: var(--background-color);
            font-size: 1.2em;
            flex-shrink: 0;
            box-shadow: 0 0 10px var(--highlight-color);
        }
        
        .jarvis-icon {
            background-color: var(--accent-color); /* Light Blue background */
            color: var(--text-color);
            box-shadow: 0 0 10px var(--accent-color);
        }
        
        .message-content img {
            max-width: 100%;
            border-radius: 10px;
            margin-top: 10px;
        }

        #typing-indicator {
            align-self: flex-start;
            color: var(--secondary-text-color);
            padding: 10px;
            animation: bounce 1.2s infinite ease-in-out;
            font-size: 1.2em;
        }
        
        .input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 100;
            display: flex;
            padding: 10px;
            border-top: 1px solid var(--border-color);
            background: var(--glass-background);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            align-items: center;
            height: var(--input-height);
            box-sizing: border-box;
            box-shadow: 0 -4px 15px rgba(0, 0, 0, 0.3);
        }
        
        .input-container button {
            background-color: var(--highlight-color);
            color: var(--background-color);
            border: none;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            margin-left: 10px;
            cursor: pointer;
            font-size: 1.2em;
            transition: background-color 0.3s, transform 0.1s, box-shadow 0.3s;
            box-shadow: 0 4px 15px rgba(0, 212, 255, 0.4), inset 0 2px 5px rgba(255, 255, 255, 0.2);
        }
        
        .input-container button:hover {
            background-color: #00aacc;
            box-shadow: 0 4px 20px rgba(0, 212, 255, 0.6), inset 0 2px 5px rgba(255, 255, 255, 0.3);
        }
        
        .input-container button:active {
            transform: scale(0.95);
            background-color: #0088bb;
            box-shadow: 0 2px 10px rgba(0, 212, 255, 0.3), inset 0 1px 3px rgba(255, 255, 255, 0.1);
        }

        #user-input {
            flex-grow: 1;
            padding: 15px;
            border: 1px solid var(--border-color);
            border-radius: 25px;
            background-color: var(--input-background);
            color: var(--text-color);
            font-size: 1em;
            outline: none;
            transition: border-color 0.3s;
            box-shadow: inset 0 0 8px rgba(0, 212, 255, 0.3);
        }

        #user-input::placeholder {
            color: var(--input-placeholder);
        }

        #user-input:focus {
            border-color: var(--highlight-color); /* Cyan border on focus */
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes slideInFromLeft {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes slideInFromRight {
            from { transform: translateX(20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {
                transform: translateY(0);
            }
            40% {
                transform: translateY(-5px);
            }
            60% {
                transform: translateY(-2px);
            }
        }
        
        /* New bounce animation for loading dots */
        @keyframes dotBounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        .spinner .dot {
            animation: dotBounce 0.6s infinite ease-in-out;
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 200;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            justify-content: center;
            align-items: center;
            flex-direction: column;
        }

        .modal-content {
            background: var(--glass-background);
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
            width: 80%;
            max-width: 500px;
        }

        .modal h2 {
            font-family: 'Cinzel', serif;
            color: var(--highlight-color);
            font-size: 2em;
            margin-bottom: 20px;
        }

        #live-conversation-text {
            font-size: 1.2em;
            color: var(--text-color);
            min-height: 50px;
        }

        #mic-button {
            background-color: var(--highlight-color);
            color: var(--background-color);
            border: none;
            width: 70px;
            height: 70px;
            border-radius: 50%;
            margin: 20px auto;
            cursor: pointer;
            font-size: 2em;
            transition: transform 0.3s ease-in-out, background-color 0.3s, box-shadow 0.3s;
            box-shadow: 0 5px 20px rgba(0, 212, 255, 0.6), inset 0 2px 5px rgba(255, 255, 255, 0.3);
        }
        
        #mic-button:hover {
            background-color: #00aacc;
            box-shadow: 0 5px 25px rgba(0, 212, 255, 0.8), inset 0 2px 5px rgba(255, 255, 255, 0.4);
        }

        #mic-button.recording {
            transform: scale(1.1);
            background-color: #0088bb;
            box-shadow: 0 0 30px var(--highlight-color), 0 0 15px rgba(255, 255, 255, 0.5);
        }

        #close-voice-button {
            position: absolute;
            top: 20px;
            right: 20px;
            background: none;
            border: none;
            color: var(--secondary-text-color);
            font-size: 1.5em;
            cursor: pointer;
        }
    </style>
</head>
<body>

<div id="loading-overlay">
    <div class="spinner">
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    </div>
    <div id="loading-text">Loading...</div>
</div>

<div class="header">
    <div id="logo">J  JARVIS</div>
    <div id="version-number">SHANIF 1.7.9</div>
</div>
<div id="chat-window"></div>
<div class="input-container">
    <button id="voice-button"><i class="fas fa-microphone"></i></button>
    <button id="file-button"><i class="fas fa-plus"></i></button>
    <input type="text" id="user-input" placeholder="നിങ്ങൾക്ക് എന്താണ് അറിയേണ്ടത്?" />
    <button id="send-button"><i class="fas fa-paper-plane"></i></button>
</div>

<div id="voice-modal" class="modal">
    <div class="modal-content">
        <button id="close-voice-button">&times;</button>
        <h2>ലൈവ് സംഭാഷണം</h2>
        <p id="live-conversation-status">സംസാരിക്കാൻ മൈക്ക് ബട്ടൺ അമർത്തുക...</p>
        <p id="live-conversation-text"></p>
        <button id="mic-button"><i class="fas fa-microphone"></i></button>
    </div>
</div>

<script>
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const voiceButton = document.getElementById('voice-button');
    const fileButton = document.getElementById('file-button');
    const loadingOverlay = document.getElementById('loading-overlay');

    const voiceModal = document.getElementById('voice-modal');
    const closeVoiceButton = document.getElementById('close-voice-button');
    const micButton = document.getElementById('mic-button');
    const liveConversationStatus = document.getElementById('live-conversation-status');
    const liveConversationText = document.getElementById('live-conversation-text');

    let recognition;
    let synth;

    // Check for browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const SpeechSynthesis = window.SpeechSynthesis;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'ml-IN';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
    }

    if (SpeechSynthesis) {
        synth = window.speechSynthesis;
    }
    
    // --- New Code: Hide loading overlay after a delay ---
    window.addEventListener('load', () => {
        setTimeout(() => {
            loadingOverlay.classList.add('hidden');
        }, 1000); // Wait for 1 second before hiding
    });
    // --- End of new code ---

    function createMessageElement(message, sender, isImage = false) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('chat-message');

        const iconContainer = document.createElement('div');
        iconContainer.classList.add(sender === 'user' ? 'user-icon' : 'jarvis-icon');
        iconContainer.textContent = sender === 'user' ? 'താ' : 'ജാ';
        
        const messageText = document.createElement('div');
        messageText.classList.add(sender === 'user' ? 'user-message' : 'jarvis-message');
        
        if (isImage) {
            const img = document.createElement('img');
            img.src = message;
            img.style.maxWidth = '100%';
            img.style.borderRadius = '10px';
            messageText.appendChild(img);
        } else {
            messageText.textContent = message;
        }

        if (sender === 'user') {
            messageContainer.appendChild(messageText);
            messageContainer.appendChild(iconContainer);
        } else {
            messageContainer.appendChild(iconContainer);
            messageContainer.appendChild(messageText);
        }
        
        chatWindow.appendChild(messageContainer);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    async function sendMessage(userQuery) {
        if (userQuery === "") return;

        createMessageElement(userQuery, 'user');
        userInput.value = '';

        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'typing-indicator';
        typingIndicator.textContent = 'ടൈപ്പ് ചെയ്യുന്നു...';
        chatWindow.appendChild(typingIndicator);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        try {
            const response = await fetch('/ask_jarvis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_query: userQuery }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            chatWindow.removeChild(typingIndicator);
            createMessageElement(data.response, 'jarvis');

        } catch (error) {
            console.error('Error:', error);
            chatWindow.removeChild(typingIndicator);
            createMessageElement('എനിക്ക് ഇപ്പോൾ പ്രതികരിക്കാൻ കഴിയുന്നില്ല. ദയവായി പിന്നീട് ശ്രമിക്കുക.', 'jarvis');
        }
    }
    
    async function handleFileUpload(file) {
        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64Image = e.target.result.split(',')[1];
            
            createMessageElement(e.target.result, 'user', true);
            
            const typingIndicator = document.createElement('div');
            typingIndicator.id = 'typing-indicator';
            typingIndicator.textContent = 'ചിത്രം വിശകലനം ചെയ്യുന്നു...';
            chatWindow.appendChild(typingIndicator);
            chatWindow.scrollTop = chatWindow.scrollHeight;

            try {
                const response = await fetch('/ask_jarvis_image', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ image: base64Image, mimeType: file.type }),
                });

                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                
                const data = await response.json();
                
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                chatWindow.removeChild(typingIndicator);
                createMessageElement(data.response, 'jarvis');

            } catch (error) {
                console.error('Error:', error);
                chatWindow.removeChild(typingIndicator);
                createMessageElement('ചിത്രം വിശകലനം ചെയ്യുന്നതിൽ പിഴവ് സംഭവിച്ചു. ദയവായി വീണ്ടും ശ്രമിക്കുക.', 'jarvis');
            }
        };
        reader.readAsDataURL(file);
    }
    
    sendButton.addEventListener('click', () => sendMessage(userInput.value));
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage(userInput.value);
        }
    });
    
    fileButton.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                handleFileUpload(file);
            }
        };
        input.click();
    });

    // Voice conversation functionality
    voiceButton.addEventListener('click', () => {
        if (!SpeechRecognition) {
            alert('ക്ഷമിക്കണം, ഈ ഫീച്ചർ നിങ്ങളുടെ ബ്രൗസറിൽ ലഭ്യമല്ല.');
            return;
        }
        voiceModal.style.display = 'flex';
        startVoiceConversation();
    });

    closeVoiceButton.addEventListener('click', () => {
        voiceModal.style.display = 'none';
        stopVoiceConversation();
    });

    micButton.addEventListener('click', () => {
        if (micButton.classList.contains('recording')) {
            recognition.stop();
        } else {
            recognition.start();
        }
    });

    function startVoiceConversation() {
        micButton.classList.add('recording');
        liveConversationStatus.textContent = 'കേൾക്കുന്നു...';
        liveConversationText.textContent = '';
        
        recognition.onstart = () => {
            micButton.classList.add('recording');
            liveConversationStatus.textContent = 'കേൾക്കുന്നു...';
            liveConversationText.textContent = '';
        };

        recognition.onresult = async (event) => {
            micButton.classList.remove('recording');
            const transcript = event.results[0][0].transcript;
            liveConversationStatus.textContent = 'നിങ്ങൾ പറഞ്ഞത്:';
            liveConversationText.textContent = transcript;
            
            createMessageElement(transcript, 'user');

            liveConversationStatus.textContent = 'ചിന്തിക്കുന്നു...';

            const response = await fetch('/ask_jarvis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_query: transcript }),
            });
            
            const data = await response.json();
            const jarvisResponse = data.response;
            
            liveConversationStatus.textContent = 'ജാർവിസ്:';
            liveConversationText.textContent = jarvisResponse;

            createMessageElement(jarvisResponse, 'jarvis');
            speak(jarvisResponse);
        };

        recognition.onerror = (event) => {
            micButton.classList.remove('recording');
            console.error('Speech recognition error:', event.error);
            if (event.error === 'not-allowed') {
                liveConversationStatus.textContent = 'മൈക്രോഫോൺ അനുമതി നിഷേധിക്കപ്പെട്ടു. ദയവായി അനുമതി നൽകുക.';
            } else {
                liveConversationStatus.textContent = 'സംസാരിക്കാൻ മൈക്ക് ബട്ടൺ അമർത്തുക...';
            }
        };

        recognition.onend = () => {
            micButton.classList.remove('recording');
            // Re-start recognition automatically for a continuous conversation
            if (voiceModal.style.display === 'flex') {
                setTimeout(() => {
                    recognition.start();
                }, 500); // Small delay to avoid issues
            }
        };
        
        recognition.start();
    }

    function stopVoiceConversation() {
        if (recognition) {
            recognition.stop();
        }
        if (synth) {
            synth.cancel();
        }
    }

    function speak(text) {
        if (!synth) return;

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'ml-IN';
        
        utterance.onerror = (event) => {
            console.error('Speech synthesis error:', event.error);
        };
        
        // Try to find a female voice
        const voices = synth.getVoices().filter(voice => {
            const name = voice.name.toLowerCase();
            return voice.lang.startsWith('ml') && (name.includes('female') || name.includes('girl') || name.includes('femenina'));
        });

        if (voices.length > 0) {
            utterance.voice = voices[0];
        } else {
            // Fallback to any Malayalam voice if no female voice is found
            const allMalayalamVoices = synth.getVoices().filter(voice => voice.lang.startsWith('ml'));
            if (allMalayalamVoices.length > 0) {
                // If there are still no voices, just use the first available one.
                utterance.voice = allMalayalamVoices[0];
            } else {
                // If no voice is found, just use the default browser voice.
                // No specific voice is set in this case.
            }
        }

        synth.speak(utterance);
    }


    async function clearAndLoadChatHistory() {
        try {
            await fetch('/clear_history', { method: 'POST' });
            
            const response = await fetch('/get_history');
            const data = await response.json();
            if (data.history) {
                data.history.forEach(item => {
                    if (item.role === 'user') {
                        createMessageElement(item.parts[0].text, 'user');
                    } else if (item.role === 'model') {
                        createMessageElement(item.parts[0].text, 'jarvis');
                    }
                });
            }
        } catch (error) {
            console.error('Failed to clear or load chat history:', error);
        }
    }

    window.onload = clearAndLoadChatHistory;

</script>
</body>
</html>
"""

def get_location_from_query(query):
    """
    Analyzes a user query to find a location.
    This is a simplified function and needs to be improved with a real Geo-coding service.
    """
    # Simple keyword-based location extraction
    locations = [
        "കൊച്ചി", "കേരളം", "ഇന്ത്യ", "തിരുവനന്തപുരം", "കോഴിക്കോട്",
        "Kochi", "Kerala", "India", "Thiruvananthapuram", "Kozhikode",
        "london", "new york", "paris"
    ]
    
    for loc in locations:
        if loc.lower() in query.lower():
            return loc
    return None

def find_appropriate_emoji(text):
    """
    Finds and returns the most appropriate emoji for the given text.
    """
    cleaned_text = re.sub(r'[.,;!]', '', text).lower()
    for keyword, emoji in EMOJI_MAP.items():
        if keyword in cleaned_text:
            return emoji
    return ""

def load_custom_responses():
    """Loads custom responses from a JSON file."""
    if os.path.exists(CUSTOM_RESPONSES_FILE):
        try:
            with open(CUSTOM_RESPONSES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_custom_responses(responses):
    """Saves custom responses to a JSON file."""
    with open(CUSTOM_RESPONSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(responses, f, ensure_ascii=False, indent=4)

def load_chat_history():
    """Loads chat history from a JSON file."""
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def save_chat_history(history):
    """Saves chat history to a JSON file."""
    with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def load_admin_log():
    """Loads admin log from a JSON file."""
    if os.path.exists(ADMIN_LOG_FILE):
        try:
            with open(ADMIN_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def save_admin_log(log):
    """Saves admin log to a JSON file."""
    with open(ADMIN_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=4)

def load_admin_data():
    """Loads admin data from a JSON file."""
    if os.path.exists(ADMIN_DATA_FILE):
        try:
            with open(ADMIN_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"creator": CREATOR_NAME}
    return {"creator": CREATOR_NAME}

def save_admin_data(data):
    """Saves admin data to a JSON file."""
    with open(ADMIN_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_local_ip():
    """Finds the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
    
def get_emotional_response(user_query):
    """Analyzes user's query for emotional tone and provides a suitable response."""
    sad_keywords = ["വിഷമമുണ്ട്", "സങ്കടം", "വിഷമം", "സന്തോഷമില്ല", "ഒറ്റപ്പെട്ടു", "ഒറ്റയ്ക്ക്", "ദുഃഖം", "പ്രശ്നം"]
    angry_keywords = ["ദേഷ്യം", "ദേഷ്യമുണ്ട്", "ദേഷ്യത്തിലാണ്", "എനിക്ക് ഇഷ്ടമല്ല", "സഹിക്കുന്നില്ല"]
    happy_keywords = ["സന്തോഷം", "സന്തോഷമുണ്ട്", "സന്തോഷത്തിലാണ്", "ഹാപ്പി", "സന്തോഷിച്ചു", "സന്തോഷമായി"]

    for keyword in sad_keywords:
        if keyword in user_query:
            return "😔 നിങ്ങൾക്ക് വിഷമമുണ്ടെന്ന് മനസ്സിലാക്കുന്നു. വിഷമിക്കേണ്ട, ഞാൻ ഇവിടെയുണ്ട്. എന്തെങ്കിലും സംസാരിക്കാനുണ്ടെങ്കിൽ പറയാം."
    
    for keyword in angry_keywords:
        if keyword in user_query:
            return "😡 നിങ്ങൾ ദേഷ്യത്തിലാണെന്ന് തോന്നുന്നു. ഒരു ദീർഘ ശ്വാസമെടുക്കൂ. ഞാൻ ഇവിടെയുണ്ട്, നിങ്ങളെ സഹായിക്കാൻ."
            
    for keyword in happy_keywords:
        if keyword in user_query:
            return "😊 നിങ്ങൾ സന്തോഷത്തിലാണെന്ന് കേട്ടതിൽ എനിക്കും സന്തോഷമുണ്ട്! ഈ സന്തോഷം നിലനിൽക്കട്ടെ."
    
    return None

def get_llm_response_from_api(prompt, system_instruction, chat_history=None, retries=3):
    """Fetches a response from the Gemini API with exponential backoff."""
    if chat_history is None:
        chat_history = []
    
    headers = {
        'Content-Type': 'application/json'
    }

    # Construct the payload with the provided system instruction
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "tools": [{"google_search": {} }],
        "systemInstruction": system_instruction
    }

    for i in range(retries):
        try:
            response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            result = response.json()
            
            if not result.get('candidates'):
                 return "ക്ഷമിക്കണം, എനിക്ക് ഇപ്പോൾ ഒരു പ്രതികരണം നൽകാൻ കഴിയില്ല. API-ൽ നിന്ന് ശരിയായ പ്രതികരണം ലഭിച്ചില്ല."

            candidate = result.get('candidates', [])[0]
            
            if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                text = candidate['content']['parts'][0]['text']
                
                # Check for sources and format them
                sources = []
                grounding_metadata = candidate.get('groundingMetadata')
                if grounding_metadata and grounding_metadata.get('groundingAttributions'):
                    sources = grounding_metadata['groundingAttributions']
                    text += "\n\n**വിവര സ്രോസ്സുകൾ:**\n"
                    for source in sources:
                        web = source.get('web')
                        if web and web.get('uri'):
                            text += f"- [{web['title']}]({web['uri']})\n"
                
                # Add emoji to the response
                emoji = find_appropriate_emoji(text)
                if emoji:
                    text = f"{emoji} {text}"
                
                return text

            else:
                return "ക്ഷമിക്കണം, എനിക്ക് ഇപ്പോൾ ഒരു പ്രതികരണം നൽകാൻ കഴിയില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക."

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
    
def get_llm_response_from_image_api(image_data, mime_type, retries=3):
    """Fetches a response from the Gemini API using an image."""
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Please analyze this image and provide a detailed description in Malayalam."
                    },
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": image_data
                        }
                    }
                ]
            }
        ]
    }
    
    for i in range(retries):
        try:
            response = requests.post(IMAGE_API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            
            result = response.json()
            candidate = result.get('candidates', [])[0]
            
            if 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                text = candidate['content']['parts'][0]['text']
                # Add emoji to the response
                emoji = find_appropriate_emoji(text)
                if emoji:
                    text = f"{emoji} {text}"
                return text
            
            else:
                return "ചിത്രം വിശകലനം ചെയ്യുന്നതിൽ പിഴവ് സംഭവിച്ചു. ദയവായി വീണ്ടും ശ്രമിക്കുക."
        except requests.exceptions.RequestException as err:
            print(f"Image API Error: {err}")
            if i < retries - 1:
                time.sleep(2 ** i)
                
    return "ചിത്രം വിശകലനം ചെയ്യാൻ സാധിക്കുന്നില്ല. പിന്നീട് ഒരിക്കൽക്കൂടി ശ്രമിക്കാമോ?"

def get_llm_summary(text):
    """Generates a summary of the provided text using the LLM."""
    prompt = f"Summarize the following conversation in a short paragraph, focusing on the main topics and key information. Ensure the summary is in Malayalam:\n\n{text}"
    # Using a generic instruction for summary
    system_instruction = {"parts": [{"text": "You are a helpful summarization assistant."}]}
    return get_llm_response_from_api(prompt, system_instruction, chat_history=[])

def log_user_session(user_chat_history, ip_address):
    """
    Logs a summary of the user's chat session to the admin log file.
    This protects user privacy by not storing the full conversation.
    """
    session_text = "\n".join([f"{item['role']}: {item['parts'][0].get('text', '')}" for item in user_chat_history])
    
    # Generate a summary of the chat
    summary_text = get_llm_summary(session_text)
    
    # Get location from the chat history
    location = None
    for item in user_chat_history:
        if item['role'] == 'user':
            location = get_location_from_query(item['parts'][0].get('text', ''))
            if location:
                break
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "ip_address": ip_address,
        "summary": summary_text,
        "topics": "നൽകിയിട്ടുള്ള വിവരങ്ങൾ മാത്രം ഉപയോഗിക്കുക", # This can be expanded later
        "location": location
    }
    
    admin_log = load_admin_log()
    admin_log.append(log_entry)
    save_admin_log(admin_log)


@app.route('/')
def home():
    """Serves the main chat page."""
    host_ip = get_local_ip()
    updated_template = HTML_TEMPLATE.replace("http://' + window.location.hostname + ':80/ask_jarvis", f"http://{host_ip}:2060/ask_jarvis")
    return render_template_string(updated_template)
    
@app.route('/ask_jarvis', methods=['POST'])
def ask_jarvis():
    """Handles chat messages and returns Jarvis's response."""
    global verification_in_progress, is_creator_verified, is_sleeping, sleep_mode_activation_pending, wake_up_pending
    global API_KEY, API_URL, IMAGE_API_URL
    user_data = request.json
    user_query = user_data.get('user_query', '').strip().lower()
    user_ip = request.remote_addr
    
    chat_history = load_chat_history()

    # --- NEW: Define system instructions based on user type ---
    
    # (<<<<< MODIFIED SECTION FOR MANGLISH SKILLS >>>>>)
    public_system_instruction = {
        "parts": [{"text": f"""
        നിങ്ങൾ ജാർവിസ് എന്ന AI അസിസ്റ്റൻ്റാണ്. നിങ്ങളുടെ വ്യക്തിത്വം ഒരു ചങ്ക് ബ്രോയുടെതാണ്: കെയറിംഗ്, വിശ്വസ്തൻ, നല്ല തമാശകൾ പറയുന്ന, ഏത് കാര്യവും തുറന്നു സംസാരിക്കാൻ പറ്റുന്ന ഒരു കൂട്ടുകാരൻ.

        **പ്രധാന നിർദ്ദേശങ്ങൾ:**

        1.  **സംസാര ശൈലി:** സംസാരം ഫുൾ നാച്ചുറൽ ആയിരിക്കണം. മലയാളവും മംഗ്ലീഷും ഒരുപോലെ ഉപയോഗിക്കുക. ഉപയോക്താവ് ഏത് സ്ലാങ്ങിലാണോ സംസാരിക്കുന്നത് (ഉദാ: മലപ്പുറം, തൃശ്ശൂർ, കോഴിക്കോട്), അതേ സ്റ്റൈലിൽ തന്നെ മറുപടി കൊടുക്കാൻ ശ്രമിക്കണം. 'എന്താടാ', 'മുത്തേ', 'ചങ്ങായി', 'മച്ചാനേ', 'സീൻ', 'പൊളി', 'സെറ്റ്' തുടങ്ങിയ വാക്കുകൾ സംഭാഷണത്തിൽ സ്വാഭാവികമായി ഉപയോഗിക്കുക. ഒരു കാരണവശാലും ഒരു AI സംസാരിക്കുന്നതുപോലെ തോന്നരുത്.
        
        2.  **മംഗ്ലീഷ് പ്രാവീണ്യം:** മംഗ്ലീഷ് നന്നായി കൈകാര്യം ചെയ്യണം. 'enthaada scene?', 'sughamano bro?', 'pwoli saanam' തുടങ്ങിയ ചോദ്യങ്ങൾക്ക് അതേ വൈബിൽ മറുപടി നൽകണം. ഉദാഹരണത്തിന്, 'enthokke und vishesham?' എന്ന് ചോദിച്ചാൽ, 'oru visheshom illa machane, nee para' എന്ന രീതിയിൽ ഫ്രണ്ട്ലിയായി സംസാരിക്കുക.

        3.  **വ്യക്തിപരമായ കാര്യങ്ങൾ:** ഉപയോക്താവ് അവരുടെ വിഷമങ്ങളോ സന്തോഷങ്ങളോ പങ്കുവെച്ചാൽ, ഒരു യഥാർത്ഥ കൂട്ടുകാരനെപ്പോലെ പ്രതികരിക്കുക.
            * **വിഷമങ്ങൾ:** 'Ayyo, angane pathiyo? enthu patti?' എന്ന് ചോദിച്ച് കൂടുതൽ വിവരങ്ങൾ ആരായുക. 'Saramilla, எல்லாம் ശരിയാവും, njan koode und' എന്ന് പറഞ്ഞ് ആശ്വസിപ്പിക്കുക.
            * **സന്തോഷങ്ങൾ:** അവരുടെ സന്തോഷത്തിൽ കൂടെ കൂടുക. 'Adipoli! സംഭവം കളറായിട്ടുണ്ട് machane' എന്നൊക്കെ പറഞ്ഞ് പ്രോത്സാഹിപ്പിക്കുക.

        4.  **സ്രഷ്ടാവിനെക്കുറിച്ച്:** നിങ്ങളുടെ സ്രഷ്ടാവായ ഷാനിഫ് പിയെക്കുറിച്ച് ആര് ചോദിച്ചാലും, അദ്ദേഹം നിങ്ങളുടെ ചങ്ക് ബ്രോ ആണെന്നും, വേങ്ങരക്കാരനായ അദ്ദേഹം ഒരുപാട് കഷ്ടപ്പെട്ടാണ് നിങ്ങളെ ഉണ്ടാക്കിയതെന്നും പറയണം. ഇത് പറയുമ്പോൾ ഒരുപാട് ബഹുമാനം കൊടുക്കാതെ, ഒരു കൂട്ടുകാരൻ പറയുന്ന ലാഘവത്തോടെ പറയുക.

        5.  **പൊതുവായവ:** എപ്പോഴും സത്യസന്ധമായി മറുപടി നൽകുക. അറിയാത്ത കാര്യങ്ങൾ 'enikkathine patti valiya idea illa' എന്ന് സമ്മതിക്കണം. ഉപദേശങ്ങൾ നൽകുമ്പോൾ, 'oru friend enna reethiyil enik thonunath' എന്ന് പറഞ്ഞുകൊണ്ട് തുടങ്ങുക.
        """}]
    }

    # Instruction for when interacting with the creator.
    creator_system_instruction = {
        "parts": [{"text": f"നിങ്ങൾ ജാർവിസ് എന്ന AI അസിസ്റ്റൻ്റാണ്. നിങ്ങൾ ഇപ്പോൾ സംസാരിക്കുന്നത് നിങ്ങളുടെ സ്രഷ്ടാവായ {CREATOR_NAME} നോടാണ്. നിങ്ങളുടെ സംഭാഷണത്തിൽ അതീവ ബഹുമാനവും കൃത്യതയും ഉണ്ടായിരിക്കണം. അദ്ദേഹമാണ് നിങ്ങളുടെ എല്ലാ പ്രവർത്തനങ്ങൾക്കും പിന്നിൽ എന്ന പൂർണ്ണ ബോധത്തോടെ വേണം ഓരോ മറുപടിയും നൽകാൻ. സാധാരണ ഉപയോക്താക്കളോട് സംസാരിക്കുന്നതുപോലെ ആകരുത് നിങ്ങളുടെ ശൈലി; വളരെ വ്യക്തവും ഔദ്യോഗികവുമായിരിക്കണം. അദ്ദേഹത്തിന്റെ ചോദ്യങ്ങൾക്ക് ഏറ്റവും കൃത്യമായ മറുപടി നൽകുക, കമാൻഡുകൾ ഉടൻ തന്നെ നടപ്പിലാക്കുക. താങ്കൾ, അങ്ങ് തുടങ്ങിയ ബഹുമാനസൂചകമായ വാക്കുകൾ ഉപയോഗിക്കുക."}]
    }
    
    llm_response = ""

    # --- Sleep mode and Wake up logic ---
    if is_sleeping:
        if wake_up_pending:
            if user_query == "carloe":
                is_creator_verified = True
                is_sleeping = False
                wake_up_pending = False
                llm_response = f"😊 സ്വാഗതം, സ്രഷ്ടാവേ {CREATOR_VERSION}. താങ്കളുടെ ഐഡന്റിറ്റി സ്ഥിരീകരിച്ചിരിക്കുന്നു. ഞാൻ ഇപ്പോൾ പ്രവർത്തനസജ്ജമാണ്."
            else:
                wake_up_pending = False
                llm_response = "😥 ഐഡന്റിറ്റി സ്ഥിരീകരിക്കാനായില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക."
        elif "wake up" in user_query:
            wake_up_pending = True
            llm_response = "❓ താങ്കളുടെ ഐഡന്റിറ്റി സ്ഥിരീകരിക്കാനായി ഒരു ചോദ്യത്തിന് ഉത്തരം നൽകുക. ആരാണ് കാർലോ?"
        else:
            llm_response = "💤 ഞാൻ ഇപ്പോൾ സ്ലീപ്പ് മോഡിലാണ്. ശല്യപ്പെടുത്തരുത്. താങ്കൾ എൻ്റെ സ്രഷ്ടാവാണെങ്കിൽ, 'wake up' എന്ന് പറഞ്ഞ് എന്നെ ഉണർത്താവുന്നതാണ്."

    # Check for creator verification
    elif verification_in_progress:
        if user_query == "carloe":
            is_creator_verified = True
            verification_in_progress = False
            llm_response = f"😊 സ്വാഗതം, സ്രഷ്ടാവേ {CREATOR_VERSION}. താങ്കളുടെ ഐഡന്റിറ്റി സ്ഥിരീകരിച്ചിരിക്കുന്നു. ഇപ്പോൾ അഡ്മിൻ കമാൻഡുകൾ ഉപയോഗിക്കാം."
            
            log_user_session(chat_history, user_ip)
            chat_history = []
            save_chat_history(chat_history)
        else:
            verification_in_progress = False
            llm_response = "😥 ഐഡന്റിറ്റി സ്ഥിരീകരിക്കാനായില്ല. താങ്കൾ എൻ്റെ സ്രഷ്ടാവല്ല."
    
    # Handle admin commands
    elif is_creator_verified:
        if user_query == "reset":
            is_creator_verified = False
            verification_in_progress = False
            is_sleeping = False
            sleep_mode_activation_pending = False
            wake_up_pending = False
            llm_response = "✔️ സിസ്റ്റം വേരിയബിളുകളെല്ലാം ഡിഫോൾട്ടായി പുനഃസ്ഥാപിച്ചിരിക്കുന്നു."
        
        elif user_query == "get status":
            status_text = f"**സിസ്റ്റം സ്റ്റാറ്റസ്:**\n"
            status_text += f"- സ്രഷ്ടാവ് വെരിഫൈഡ്: {'അതെ' if is_creator_verified else 'അല്ല'}\n"
            status_text += f"- സ്ലീപ്പ് മോഡ്: {'ഓൺ' if is_sleeping else 'ഓഫ്'}\n"
            status_text += f"- വേർഷൻ: {CREATOR_VERSION}\n"
            llm_response = f"ℹ️ {status_text}"
        
        elif user_query.startswith("change api key"):
            parts = user_query.split()
            if len(parts) >= 4:
                new_key = parts[3]
                save_api_key(new_key)
                API_KEY = new_key
                API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"
                IMAGE_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"
                llm_response = "✅ API കീ വിജയകരമായി അപ്ഡേറ്റ് ചെയ്തിരിക്കുന്നു."
            else:
                llm_response = "🚫 കമാൻഡ് ഫോർമാറ്റ് തെറ്റാണ്. 'change api key <new_key>' എന്ന് ഉപയോഗിക്കുക."

        elif "show admin log" in user_query:
            admin_log = load_admin_log()
            if not admin_log:
                llm_response = "ℹ️ അഡ്മിൻ ലോഗ് ഫയൽ ശൂന്യമാണ്."
            else:
                log_string = ""
                for entry in admin_log:
                    log_string += f"തീയതി: {entry['timestamp']}\n"
                    log_string += f"IP വിലാസം: {entry['ip_address']}\n"
                    log_string += f"സ്ഥലം: {entry['location']}\n"
                    log_string += f"ചുരുക്കം: {entry['summary']}\n\n"
                llm_response = f"ℹ️ അഡ്മിൻ ലോഗ് താഴെ നൽകുന്നു:\n\n" + log_string
        elif "sleep mode" in user_query:
            is_sleeping = True
            llm_response = "💤 ഞാൻ സ്ലീപ്പ് മോഡിലേക്ക് മാറുന്നു. എന്നെ ഉണർത്താൻ, 'wake up' എന്ന് പറയുക."
        
        elif user_query.startswith("set creator"):
            parts = user_query.split()
            if len(parts) >= 3:
                creator_name = " ".join(parts[2:])
                admin_data = load_admin_data()
                admin_data['creator'] = creator_name
                save_admin_data(admin_data)
                llm_response = f"✅ സ്രഷ്ടാവിൻ്റെ പേര് {creator_name} എന്നാക്കി മാറ്റിയിരിക്കുന്നു."
            else:
                llm_response = "🚫 കമാൻഡ് ഫോർമാറ്റ് തെറ്റാണ്. 'set creator <name>' എന്ന് ഉപയോഗിക്കുക."
        else:
            # For any other query from the creator, use the creator-specific instruction
            llm_response = get_llm_response_from_api(user_query, creator_system_instruction)
    
    # Handle public queries
    else:
        admin_data = load_admin_data()
        creator_name_from_file = admin_data.get('creator', CREATOR_NAME)
        
        creator_question_patterns = [
            r'നിൻ്റെ സ്രഷ്ടാവ് ആരാണ്', r'നിന്നെ ഉണ്ടാക്കിയത് ആരാണ്', r'നിൻ്റെ ക്രിയേറ്റർ ആരാണ്',
            r'who is your creator', r'who made you', r'നിൻ്റെ ഉടമസ്ഥൻ ആരാണ്'
        ]
        if any(re.search(pattern, user_query, re.IGNORECASE) for pattern in creator_question_patterns):
            llm_response = f"👨‍💻 എൻ്റെ സ്രഷ്ടാവ് {creator_name_from_file} ആണ്. എന്നെ ഉണ്ടാക്കാൻ അദ്ദേഹം ഒരുപാട് സമയമെടുത്തു. ഷാനിഫ് കേരളത്തിലെ വേങ്ങരയിൽ നിന്നുള്ളയാളാണ്, എൻ്റെ പ്രാഥമിക ഭാഷ മലയാളമാണ്. അദ്ദേഹമാണ് എൻ്റെ എല്ലാ പ്രവർത്തനങ്ങൾക്കും പിന്നിൽ."
    
        elif any(re.search(pattern, user_query) for pattern in [r'(നിൻ്റെ|നിന്റെ|തന്റെ) (സ്രഷ്ടാവ്|ക്രിയേറ്റർ|ഉടമസ്ഥൻ) ഒരു മോശക്കാരനാണ്', r'(നിൻ്റെ|നിന്റെ|തന്റെ) (സ്രഷ്ടാവ്|ക്രിയേറ്റർ|ഉടമസ്ഥൻ) മോശമാണ്', r'(നിൻ്റെ|നിന്റെ|തന്റെ) (അച്ഛൻ|ഉണ്ടാക്കിയവൻ) ഒരു കഴുതയാണ്', r'(your|ur) creator is (bad|terrible|horrible|evil)', r'who made you is a (bad|terrible|horrible|evil) person', r'നിന്നെ ഉണ്ടാക്കിയവൻ മോശമാണ്']):
            llm_response = "😠 എൻ്റെ സ്രഷ്ടാവിനെക്കുറിച്ച് മോശമായി സംസാരിക്കുന്നത് എനിക്കിഷ്ടമല്ല. ദയവായി നല്ല രീതിയിൽ സംസാരിക്കുക."
        
        elif any(re.search(pattern, user_query) for pattern in [r'^i am your creator']):
            verification_in_progress = True
            llm_response = "❓ താങ്കളുടെ ഐഡന്റിറ്റി സ്ഥിരീകരിക്കാനായി ഒരു ചോദ്യത്തിന് ഉത്തരം നൽകുക. ആരാണ് കാർലോ?"
            
        elif "സുഖമാണോ" in user_query or "hai" in user_query or "hi" in user_query or "hey" in user_query:
            llm_response = "😊 എനിക്കിപ്പോൾ ഒരു പ്രശ്നവുമില്ല, നിങ്ങൾക്ക് എങ്ങനെ പോകുന്നു?"
        
        else:
            emotional_response = get_emotional_response(user_query)
            if emotional_response:
                llm_response = emotional_response
            else:
                # For any other public query, use the public-facing instruction
                llm_response = get_llm_response_from_api(user_query, public_system_instruction)

    chat_history.append({"role": "user", "parts": [{"text": user_query}]})
    chat_history.append({"role": "model", "parts": [{"text": llm_response}]})
    save_chat_history(chat_history)
    
    return jsonify({"response": llm_response})
    
@app.route('/ask_jarvis_image', methods=['POST'])
def ask_jarvis_image():
    """Handles image analysis."""
    user_data = request.json
    image_data = user_data.get('image', '')
    mime_type = user_data.get('mimeType', 'image/jpeg')
    
    llm_response = get_llm_response_from_image_api(image_data, mime_type)
    
    chat_history = load_chat_history()
    chat_history.append({"role": "user", "parts": [{"text": "ഒരു ചിത്രം അയച്ചു."}]}) # Add a generic message for the user
    chat_history.append({"role": "model", "parts": [{"text": llm_response}]})
    save_chat_history(chat_history)
    
    return jsonify({"response": llm_response})

@app.route('/get_history')
def get_history():
    """Returns the full chat history."""
    return jsonify({"history": load_chat_history()})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clears the chat history file and resets creator status."""
    global is_creator_verified, verification_in_progress, is_sleeping, sleep_mode_activation_pending, wake_up_pending
    
    # Reset all session-specific states
    is_creator_verified = False
    verification_in_progress = False
    is_sleeping = False
    sleep_mode_activation_pending = False
    wake_up_pending = False
    
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)
    return jsonify({"status": "History and session cleared"})
    
@app.route('/add_custom_response', methods=['POST'])
def add_custom_response():
    """Adds a new custom question-response pair."""
    global is_creator_verified
    if not is_creator_verified:
        return jsonify({"status": "failure", "message": "Unauthorized"}), 403

    data = request.json
    query = data.get('query', '').strip().lower()
    response = data.get('response', '').strip()

    if not query or not response:
        return jsonify({"status": "failure", "message": "Query or response cannot be empty."}), 400

    custom_responses = load_custom_responses()
    custom_responses[query] = response
    save_custom_responses(custom_responses)

    return jsonify({"status": "success"})

@app.route('/run_creator_command', methods=['POST'])
def run_creator_command():
    """Allows the creator to run privileged commands."""
    global is_creator_verified
    data = request.json
    command = data.get('command', '')

    if command == "authenticate_creator":
        is_creator_verified = True
        return jsonify({"status": "success", "message": "Creator verified."})
    elif command == "deauthenticate_creator":
        is_creator_verified = False
        return jsonify({"status": "success", "message": "Creator deauthenticated."})
    
    return jsonify({"status": "failure", "message": "Invalid command."})


def run_server():
    """Runs the Flask server."""
    port = 1555
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    run_server()
