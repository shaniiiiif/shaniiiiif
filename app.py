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
# Flask-ൽ മാറ്റം വരുത്തിയിരിക്കുന്നു: session, redirect, url_for എന്നിവ ചേർത്തു.
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for 
import socket
import base64
from datetime import datetime
import io
import zipfile
import pdfplumber

# --- New Gmail OAuth Imports ---
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from email.mime.text import MIMEText

# The file paths for chat history, creator status, and custom responses.
CHAT_HISTORY_FILE = "chat_history.json"
CREATOR_STATUS_FILE = "creator_status.json"
CUSTOM_RESPONSES_FILE = "custom_responses.json"
THEME_STATUS_FILE = "theme_status.json"
VISITS_FILE = "visits.json"
ADMIN_LOG_FILE = "admin_log.json"
ADMIN_DATA_FILE = "admin_data.json"
API_KEY_FILE = "api_key.json"
CREATOR_MEMORY_FILE = "creator_memory.json"
# --- New Gmail Token File Path ---
GMAIL_TOKEN_FILE = "gmail_token.json" 

# --- GMAIL OAuth 2.0 Configuration ---
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CLIENT_SECRET_FILE = 'credentials.json' # നിങ്ങളുടെ Google Cloud-ൽ നിന്ന് ഡൗൺലോഡ് ചെയ്ത ഫയൽ
REDIRECT_URI = 'https://shaniiiiif-5.onrender.com/oauth2callback' # <--- ഇവിടെയാണ് മാറ്റം വരുത്തിയിരിക്കുന്നത്. പുതിയ Render URL!


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
    return "AIzaSyD_yLLB4d1Dw6JhHRGqpkLlcL4VVEETDq0" # Replace with your default key if needed

def save_api_key(key):
    """Saves API key to a JSON file."""
    with open(API_KEY_FILE, 'w', encoding='utf-8') as f:
        json.dump({"api_key": key}, f, ensure_ascii=False, indent=4)

# Load the API key at startup
API_KEY = load_api_key()
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"
IMAGE_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"
TTS_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={API_URL}"

app = Flask(__name__)
# Flask സെഷൻ ഉപയോഗിക്കാൻ ഒരു സീക്രട്ട് കീ വേണം (ഇതൊരു രഹസ്യ കീ ഉപയോഗിച്ച് മാറ്റുക)
app.secret_key = 'your_super_secret_key_here' 

# Global variables to track creator status and sleeping status
is_creator_verified = False
verification_in_progress = False
is_sleeping = False
sleep_mode_activation_pending = False
wake_up_pending = False

# The creator's name and version for the AI
CREATOR_NAME = "SHANIF P"
CREATOR_VERSION = "1.7.9"

# --- Emoji Mapping ---
# ... (Emoji Mapping കോഡ് അതേപടി നിലനിർത്തുക)
EMOJI_MAP = {
    "hello": "👋", "hi": "👋", "നമസ്കാരം": "👋", "hi-tech": "⚙️", "സാങ്കേതികവിദ്യ": "⚙️",
    "കമ്പ്യൂട്ടർ": "💻", "ഫോൺ": "📱", "സന്തോഷം": "😊", "നന്ദി": "🙏", "വിഷമം": "😔",
    "സഹായിക്കാം": "🤝", "പ്രവർത്തിപ്പിക്കാം": "✔️", "ശരി": "👍", "വേണ്ട": "🚫", "ചോദ്യം": "❓",
    "പറ്റി": "💡", "ക്ഷമിക്കണം": "😥", "പോവുക": "🚶‍♂️", "യാത്ര": "✈️", "സമയം": "⏰", "തീയതി": "🗓️",
    "നിങ്ങളുടെ സ്രഷ്ടാവ്": "👨‍💻", "ഭക്ഷണം": "🍔", "വെള്ളം": "💧", "കാർ": "🚗", "എഴുതുക": "✍️",
    "കവിത": "📜", "ചിത്രം": "🖼️", "വിവരങ്ങൾ": "ℹ️", "പരിഭാഷ": "🔄", "കളി": "🎮", "പാട്ട്": "🎶",
    "weather": "🌦️", "കാലാവസ്ഥ": "🌦️", "ദേഷ്യം": "😡", "സമാധാനം": "😌", "പ്രണയം": "❤️",
    "love": "❤️", "സ്നേഹം": "❤️", "കഷ്ടം": "😓", "ആശ്ചര്യം": "😮", "തമാശ": "😂", "നല്ലത്": "👌",
    "മോശം": "👎", "വിജയം": "🏆", "ഓക്കേ": "👍", "ok": "👍", "ഓർമ്മ": "🧠", "മനസ്സിലാക്കുക": "🤔",
    "പഠിക്കുക": "📚", "പരീക്ഷണം": "🧪", "പണം": "💰", "തുറക്കുക": "📂", "അടയ്ക്കുക": "❌",
    "തുടരുക": "➡️", "തിരികെ": "🔙", "മരണപെട്ടു": "💀", "മരണം": "💀", "പുതിയത്": "✨",
    "pdf": "📄", "zip": "ZIP"
}

# --- HTML Template ---
# ... (HTML_TEMPLATE കോഡ് അതുപോലെ ഇവിടെയുണ്ട്)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ml">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ജാർവിസ് - ഷാനിഫ് 1.7.9</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&family=Orbitron:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        :root {
            --background-color: #0a0f2a;
            --glass-background: rgba(10, 15, 42, 0.75);
            --border-color: rgba(0, 123, 255, 0.3);
            --text-color: #f0f0f0;
            --secondary-text-color: #a0a0b0;
            --accent-color: #007bff;
            --highlight-color: #00d4ff;
            --input-background: rgba(25, 30, 55, 0.6);
            --input-placeholder: rgba(160, 160, 176, 0.5);
            --user-message-bg: rgba(0, 123, 255, 0.2);
            --jarvis-message-bg: rgba(40, 45, 70, 0.7);
            --header-height: 70px;
            --input-height: 70px;
        }

        body {
            font-family: 'Roboto', sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--background-color);
            background-image:
                radial-gradient(circle at 15% 50%, rgba(0, 123, 255, 0.1), transparent 40%),
                radial-gradient(circle at 85% 30%, rgba(0, 212, 255, 0.1), transparent 40%);
            height: 100vh;
            color: var(--text-color);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

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

        .spinner { display: flex; gap: 10px; }
        .dot {
            width: 15px;
            height: 15px;
            background-color: var(--highlight-color);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        
        #loading-text {
            color: var(--secondary-text-color);
            margin-top: 20px;
            font-size: 1.2em;
        }

        .header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
            text-align: center;
            padding: 15px 0;
            background-color: var(--glass-background);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            height: var(--header-height);
            box-sizing: border-box;
            border-bottom: 1px solid var(--border-color);
        }

        .logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
        }

        #logo {
            font-family: 'Orbitron', sans-serif;
            font-size: 2em;
            font-weight: 700;
            color: var(--text-color);
            text-shadow: 0 0 8px var(--accent-color);
        }
        
        #logo .fa-brain {
            color: var(--highlight-color);
            margin-right: 5px;
        }
        
        #creator-handle {
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.8em;
            color: var(--secondary-text-color);
            opacity: 0.8;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        #version-number {
            font-size: 0.7em;
            color: var(--secondary-text-color);
            margin-top: -5px;
            text-align: center;
            font-weight: bold;
            opacity: 0.7;
        }

        #chat-window {
            flex-grow: 1;
            padding: 20px;
            padding-top: calc(var(--header-height) + 10px);
            padding-bottom: calc(var(--input-height) + 10px);
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
            scrollbar-width: thin;
            scrollbar-color: var(--accent-color) transparent;
        }

        #chat-window::-webkit-scrollbar { width: 6px; }
        #chat-window::-webkit-scrollbar-track { background: transparent; }
        #chat-window::-webkit-scrollbar-thumb {
            background-color: var(--accent-color);
            border-radius: 10px;
        }

        .chat-message {
            display: flex;
            gap: 10px;
            word-wrap: break-word;
            white-space: pre-wrap;
            animation: fadeIn 0.5s ease-in-out;
        }
        
        .message-content {
            padding: 12px 18px;
            border-radius: 18px;
            max-width: 80%;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            position: relative;
            border: 1px solid transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .user-message .message-content {
            align-self: flex-end;
            background-color: var(--user-message-bg);
            color: var(--text-color);
            border-radius: 18px 18px 5px 18px;
            border-color: var(--border-color);
            animation: slideInFromRight 0.5s forwards;
        }
        
        .jarvis-message .message-content {
            align-self: flex-start;
            background-color: var(--jarvis-message-bg);
            color: var(--text-color);
            border-radius: 18px 18px 18px 5px;
            animation: slideInFromLeft 0.5s forwards;
        }
        
        .user-icon, .jarvis-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            font-size: 1.2em;
            flex-shrink: 0;
        }
        
        .user-icon {
            background-color: var(--accent-color);
            color: white;
        }
        
        .jarvis-icon {
            background-color: var(--jarvis-message-bg);
            color: var(--highlight-color);
            border: 1px solid var(--highlight-color);
        }
        
        .message-content img {
            max-width: 100%;
            border-radius: 10px;
            margin-top: 10px;
        }
        
        .typing-dots { display: flex; align-items: center; padding: 5px 0; }
        .typing-dots span {
            width: 8px;
            height: 8px;
            background-color: var(--highlight-color);
            border-radius: 50%;
            margin: 0 4px;
            animation: dot-bounce 1.4s infinite ease-in-out both;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes dot-bounce {
            0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1.0); }
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
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            align-items: center;
            height: var(--input-height);
            box-sizing: border-box;
        }
        
        .input-container .icon-button {
            background-color: transparent;
            color: var(--secondary-text-color);
            border: 1px solid var(--border-color);
            width: 45px;
            height: 45px;
            border-radius: 50%;
            margin: 0 5px;
            cursor: pointer;
            font-size: 1.1em;
            transition: all 0.3s;
        }
        
        .input-container .icon-button:hover {
            background-color: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
        }
        
        #send-button {
            background-color: var(--accent-color);
            color: white;
            border: none;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            margin-left: 10px;
            cursor: pointer;
            font-size: 1.2em;
            transition: background-color 0.3s, transform 0.1s;
        }
        #send-button:hover { background-color: #0056b3; }
        #send-button:active { transform: scale(0.95); }
        
        .speak-button {
            background: none;
            border: none;
            color: var(--secondary-text-color);
            font-size: 1.1em;
            cursor: pointer;
            transition: color 0.3s, transform 0.2s;
            opacity: 0.8;
        }
        
        .speak-button:hover { color: var(--highlight-color); opacity: 1; transform: scale(1.1); }

        #user-input {
            flex-grow: 1;
            padding: 0 20px;
            height: 45px;
            border: 1px solid var(--border-color);
            border-radius: 25px;
            background-color: var(--input-background);
            color: var(--text-color);
            font-size: 1em;
            outline: none;
            transition: border-color 0.3s, box-shadow 0.3s;
        }

        #user-input::placeholder { color: var(--input-placeholder); }
        #user-input:focus { border-color: var(--accent-color); box-shadow: 0 0 8px var(--accent-color); }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slideInFromLeft { from { transform: translateX(-20px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes slideInFromRight { from { transform: translateX(20px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes bounce { 0%, 20%, 50%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-5px); } 60% { transform: translateY(-2px); } }
        
        .modal {
            display: none; position: fixed; z-index: 200; left: 0; top: 0; width: 100%; height: 100%;
            background-color: rgba(0, 0, 0, 0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
            justify-content: center; align-items: center; flex-direction: column;
        }
        .modal-content {
            background: var(--glass-background); padding: 30px; border-radius: 20px;
            text-align: center; box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5); width: 80%; max-width: 500px;
        }
        .modal h2 { font-family: 'Orbitron', serif; color: var(--highlight-color); font-size: 2em; margin-bottom: 20px; }
        #live-conversation-text { font-size: 1.2em; color: var(--text-color); min-height: 50px; }
        #mic-button {
            background-color: var(--accent-color); color: white; border: none; width: 70px; height: 70px; border-radius: 50%;
            margin: 20px auto; cursor: pointer; font-size: 2em; transition: all 0.3s;
        }
        #mic-button:hover { background-color: #0056b3; }
        #mic-button.recording { transform: scale(1.1); background-color: #c82333; box-shadow: 0 0 20px #c82333; }
        #close-voice-button { position: absolute; top: 20px; right: 20px; background: none; border: none; color: var(--secondary-text-color); font-size: 1.5em; cursor: pointer; }
    </style>
</head>
<body>

<div id="loading-overlay">
    <div class="spinner"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
    <div id="loading-text">Loading...</div>
</div>

<div class="header">
    <div class="logo-container">
        <div id="logo"><i class="fas fa-brain"></i> JARVIS</div>
    </div>
    <div id="version-number">VERSION {{CREATOR_VERSION}}</div>
    <span id="creator-handle"><i class="fab fa-instagram"></i> @shannnniif</span>
</div>

<div id="chat-window"></div>

<div class="input-container">
    <button id="voice-button" class="icon-button"><i class="fas fa-microphone"></i></button>
    <button id="file-button" class="icon-button"><i class="fas fa-paperclip"></i></button>
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
    
    document.addEventListener('DOMContentLoaded', () => {
        loadingOverlay.classList.add('hidden');
    });

    function speakMessage(text) {
        if (!synth) { return; }
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'ml-IN';
        const malayalamVoice = synth.getVoices().find(voice => voice.lang.startsWith('ml'));
        if (malayalamVoice) { utterance.voice = malayalamVoice; }
        synth.speak(utterance);
    }

    function createMessageElement(message, sender, isImage = false) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('chat-message', sender === 'user' ? 'user-message' : 'jarvis-message');
        
        const icon = document.createElement('div');
        icon.classList.add(sender === 'user' ? 'user-icon' : 'jarvis-icon');
        icon.textContent = sender === 'user' ? 'U' : 'J';
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');

        const messageTextSpan = document.createElement('span');

        if (isImage) {
            const img = document.createElement('img');
            img.src = message;
            messageTextSpan.appendChild(img);
        } else {
            messageTextSpan.innerHTML = message.replace(/\\n/g, '<br>');
        }
        messageContent.appendChild(messageTextSpan);

        if (sender === 'jarvis' && !isImage) {
            const speakButton = document.createElement('button');
            speakButton.classList.add('speak-button');
            speakButton.innerHTML = '<i class="fas fa-volume-up"></i>';
            speakButton.onclick = (e) => {
                e.stopPropagation();
                speakMessage(message);
            };
            messageContent.appendChild(speakButton);
        }

        if (sender === 'user') {
            messageContainer.appendChild(messageContent);
            messageContainer.appendChild(icon);
        } else {
            messageContainer.appendChild(icon);
            messageContainer.appendChild(messageContent);
        }
        
        chatWindow.appendChild(messageContainer);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    async function sendMessage(userQuery) {
        if (userQuery.trim() === "") return;

        createMessageElement(userQuery, 'user');
        userInput.value = '';

        const typingIndicatorHTML = `
            <div id="typing-indicator" class="chat-message jarvis-message">
                <div class="jarvis-icon">J</div>
                <div class="message-content">
                    <div class="typing-dots"><span></span><span></span><span></span></div>
                </div>
            </div>`;
        chatWindow.insertAdjacentHTML('beforeend', typingIndicatorHTML);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        try {
            const response = await fetch('/ask_jarvis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_query: userQuery }),
            });

            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            
            document.getElementById('typing-indicator')?.remove();
            createMessageElement(data.response, 'jarvis');

        } catch (error) {
            console.error('Error:', error);
            document.getElementById('typing-indicator')?.remove();
            createMessageElement('എനിക്ക് ഇപ്പോൾ പ്രതികരിക്കാൻ കഴിയുന്നില്ല. ദയവായി പിന്നീട് ശ്രമിക്കുക.', 'jarvis');
        }
    }
    
    async function handleFileUpload(file) {
        if (!file.type.startsWith('image/')) {
            createMessageElement(`നിങ്ങൾ '${file.name}' എന്ന ഫയൽ അപ്‌ലോഡ് ചെയ്തു.`, 'user');
        }

        const typingIndicatorHTML = `
            <div id="typing-indicator" class="chat-message jarvis-message">
                <div class="jarvis-icon">J</div>
                <div class="message-content"><div class="typing-dots"><span></span><span></span><span></span></div></div>
            </div>`;
        chatWindow.insertAdjacentHTML('beforeend', typingIndicatorHTML);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64Content = e.target.result.split(',')[1];
            let endpoint = file.type.startsWith('image/') ? '/ask_jarvis_image' : '/analyze_file';
            let payload = file.type.startsWith('image/')
                ? { image: base64Content, mimeType: file.type }
                : { file_content: base64Content, file_name: file.name, mime_type: file.type };

            if (file.type.startsWith('image/')) {
                 createMessageElement(e.target.result, 'user', true);
            }

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
                const data = await response.json();
                document.getElementById('typing-indicator')?.remove();
                createMessageElement(data.response, 'jarvis');
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('typing-indicator')?.remove();
                createMessageElement('ഫയൽ വിശകലനം ചെയ്യുന്നതിൽ പിഴവ് സംഭവിച്ചു.', 'jarvis');
            }
        };
        reader.readAsDataURL(file);
    }
    
    sendButton.addEventListener('click', () => sendMessage(userInput.value));
    userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(userInput.value); });
    
    fileButton.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*, .pdf, .zip, .txt, .vcf, .py, .md, .json, .html, .css, .js'; 
        input.onchange = (e) => { if (e.target.files[0]) handleFileUpload(e.target.files[0]); };
        input.click();
    });

    voiceButton.addEventListener('click', () => {
        if (!SpeechRecognition) {
            alert('ക്ഷമിക്കണം, ഈ ഫീച്ചർ നിങ്ങളുടെ ബ്രൗസറിൽ ലഭ്യമല്ല.');
            return;
        }
        voiceModal.style.display = 'flex';
    });

    closeVoiceButton.addEventListener('click', () => {
        voiceModal.style.display = 'none';
        if (recognition) recognition.stop();
    });

    micButton.addEventListener('click', () => {
        if (micButton.classList.contains('recording')) {
            recognition.stop();
        } else {
            recognition.start();
        }
    });

    if (recognition) {
        recognition.onstart = () => { micButton.classList.add('recording'); liveConversationStatus.textContent = 'കേൾക്കുന്നു...'; };
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            liveConversationText.textContent = transcript;
            sendMessage(transcript);
        };
        recognition.onerror = (event) => { console.error('Speech recognition error:', event.error); };
        recognition.onend = () => { micButton.classList.remove('recording'); liveConversationStatus.textContent = 'സംസാരിക്കാൻ മൈക്ക് ബട്ടൺ അമർത്തുക...'; };
    }

    async function loadChatHistory() {
        try {
            const response = await fetch('/get_history');
            const data = await response.json();
            chatWindow.innerHTML = ''; // Clear window before loading
            if (data.history) {
                data.history.forEach(item => {
                    const role = item.role === 'user' ? 'user' : 'jarvis';
                    // Assuming simple text parts for history loading
                    if (item.parts && item.parts[0] && item.parts[0].text) {
                       createMessageElement(item.parts[0].text, role);
                    }
                });
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }
    
    // Clear history on new session for privacy and context reset
    async function clearHistoryOnLoad() {
        try {
            await fetch('/clear_history', { method: 'POST' });
        } catch (error) {
            console.error('Failed to clear history on load:', error);
        }
    }
    
    window.onload = clearHistoryOnLoad;

</script>
</body>
</html>
"""

# --- UTILITY FUNCTIONS ---
# ... (UTILITY FUNCTIONS കോഡ് അതുപോലെ ഇവിടെയുണ്ട്)
def get_location_from_query(query):
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
    cleaned_text = re.sub(r'[.,;!]', '', text).lower()
    for keyword, emoji in EMOJI_MAP.items():
        if keyword in cleaned_text:
            return emoji
    return ""

def load_json_file(file_path, default_value):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return default_value
    return default_value

def save_json_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_custom_responses():
    return load_json_file(CUSTOM_RESPONSES_FILE, {})

def save_custom_responses(responses):
    save_json_file(CUSTOM_RESPONSES_FILE, responses)

def load_chat_history():
    return load_json_file(CHAT_HISTORY_FILE, [])

def save_chat_history(history):
    save_json_file(CHAT_HISTORY_FILE, history)

def load_creator_memory():
    return load_json_file(CREATOR_MEMORY_FILE, [])

def save_creator_memory(history):
    save_json_file(CREATOR_MEMORY_FILE, history)

def load_admin_log():
    return load_json_file(ADMIN_LOG_FILE, [])

def save_admin_log(log):
    save_json_file(ADMIN_LOG_FILE, log)

def load_admin_data():
    return load_json_file(ADMIN_DATA_FILE, {"creator": CREATOR_NAME})

def save_admin_data(data):
    save_json_file(ADMIN_DATA_FILE, data)

def get_local_ip():
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

# --- CORE LLM FUNCTIONS ---
def get_llm_response_from_api(prompt, system_instruction, chat_history=None, retries=3):
    if chat_history is None:
        chat_history = []
    
    headers = {'Content-Type': 'application/json'}
    conversation_contents = chat_history + [{"role": "user", "parts": [{"text": prompt}]}]
    payload = {
        "contents": conversation_contents,
        "tools": [{"google_search": {} }],
        "systemInstruction": system_instruction
    }

    for i in range(retries):
        try:
            response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            
            if not result.get('candidates'):
                 return "ക്ഷമിക്കണം, എനിക്ക് ഇപ്പോൾ ഒരു പ്രതികരണം നൽകാൻ കഴിയില്ല. API-ൽ നിന്ന് ശരിയായ പ്രതികരണം ലഭിച്ചില്ല."

            candidate = result.get('candidates', [])[0]
            
            if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                text = candidate['content']['parts'][0]['text']
                emoji = find_appropriate_emoji(text)
                if emoji:
                    text = f"{emoji} {text}"
                return text
            else:
                return "ക്ഷമിക്കണം, എനിക്ക് ഇപ്പോൾ ഒരു പ്രതികരണം നൽകാൻ കഴിയുന്നില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക."
        except requests.exceptions.RequestException as err:
            print(f"API Error: {err}")
            if i < retries - 1:
                time.sleep(2 ** i)
    
    return "എനിക്കിപ്പോൾ മറുപടി തരാൻ സാധിക്കുന്നില്ല. പിന്നീട് ഒരിക്കൽക്കൂടി ശ്രമിക്കാമോ?"
    
def get_llm_response_from_image_api(image_data, mime_type, retries=3):
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [
                {"text": "Please analyze this image and provide a detailed description in Malayalam."},
                {"inlineData": {"mimeType": mime_type, "data": image_data}}
            ]
        }]
    }
    
    for i in range(retries):
        try:
            response = requests.post(IMAGE_API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            candidate = result.get('candidates', [])[0]
            
            if 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                text = candidate['content']['parts'][0]['text']
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
    prompt = f"Summarize the following conversation in a short paragraph, focusing on the main topics and key information. Ensure the summary is in Malayalam:\n\n{text}"
    system_instruction = {"parts": [{"text": "You are a helpful summarization assistant."}]}
    return get_llm_response_from_api(prompt, system_instruction, chat_history=[])

# --- GMAIL OAuth 2.0 Functions (For Web App) ---

def get_gmail_service():
    """OAuth 2.0 ടോക്കൺ ഉപയോഗിച്ച് Gmail API service ഉണ്ടാക്കുന്നു."""
    creds = None
    
    # 1. സെഷനിൽ token ഉണ്ടോ എന്ന് നോക്കുന്നു
    if 'credentials' in session:
        creds = Credentials.from_authorized_user_info(json.loads(session['credentials']), GMAIL_SCOPES)
    
    # 2. ടോക്കൺ ഫയലിൽ (gmail_token.json) ഉണ്ടോ എന്ന് നോക്കുന്നു 
    elif os.path.exists(GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, GMAIL_SCOPES)
        # ടോക്കൺ സെഷനിലേക്ക് മാറ്റുന്നു
        session['credentials'] = creds.to_json()

    # 3. ടോക്കൺ Expired ആയാൽ Refresh ചെയ്യുന്നു
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        session['credentials'] = creds.to_json()
        with open(GMAIL_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    # 4. Creds ഉണ്ടെങ്കിൽ service ഉണ്ടാക്കുന്നു
    if creds and creds.valid:
        return build('gmail', 'v1', credentials=creds)
    
    return None # Creds ഇല്ലെങ്കിൽ service ഇല്ല

def gmail_oauth_flow():
    """OAuth Flow ഉണ്ടാക്കി Authorization URL നൽകുന്നു."""
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE, GMAIL_SCOPES, redirect_uri=REDIRECT_URI)
    
    # ഇത് Google-ൻ്റെ authorization പേജിലേക്കുള്ള URL ഉണ്ടാക്കുന്നു
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    # flow object സെഷനിൽ സേവ് ചെയ്യുന്നു
    session['oauth_state'] = state
    return authorization_url

def send_email_draft(recipient, subject, body):
    """ഒരു പുതിയ ഇമെയിൽ അയക്കുന്നു."""
    service = get_gmail_service()
    if not service:
        return "🚫 Gmail-ന് അനുമതി നൽകിയിട്ടില്ല. ആദ്യം '/authorize_gmail' ഉപയോഗിച്ച് അനുമതി നൽകുക."
        
    try:
        message = MIMEText(body)
        message['to'] = recipient
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        
        return f"✅ ഇമെയിൽ വിജയകരമായി അയച്ചു! സ്വീകർത്താവ്: {recipient}, സബ്ജക്റ്റ്: {subject}"
    except Exception as e:
        return f"🚫 ഇമെയിൽ അയക്കുന്നതിൽ പിശക്: {e}. OAuth ടോക്കൺ ശരിയാണോ എന്ന് പരിശോധിക്കുക."

def get_latest_emails():
    """വായിക്കാത്ത 5 ഇമെയിലുകൾ എടുക്കുന്നു."""
    service = get_gmail_service()
    if not service:
        return "🚫 Gmail-ന് അനുമതി നൽകിയിട്ടില്ല. ആദ്യം '/authorize_gmail' ഉപയോഗിച്ച് അനുമതി നൽകുക."
        
    try:
        results = service.users().messages().list(userId='me', maxResults=5, q="is:unread").execute()
        messages = results.get('messages', [])

        if not messages:
            return "ഇപ്പോൾ വായിക്കാത്ത പുതിയ ഇമെയിലുകൾ ഒന്നും ഇല്ല."
        
        summaries = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            
            headers = msg['payload']['headers']
            # സബ്ജക്റ്റും അയച്ചയാളെയും കണ്ടെത്തുന്നു
            subject = [h['value'] for h in headers if h['name'] == 'Subject'][0] if any(h['name'] == 'Subject' for h in headers) else "No Subject"
            sender = [h['value'] for h in headers if h['name'] == 'From'][0] if any(h['name'] == 'From' for h in headers) else "Unknown Sender"
            
            summaries.append(f"✉️ അയച്ചയാൾ: {sender}\n📄 സബ്ജക്റ്റ്: {subject}")
            
            # ഇമെയിൽ വായിച്ചതായി അടയാളപ്പെടുത്തുന്നു
            service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['UNREAD']}).execute()

        return "പുതിയ 5 പ്രധാനപ്പെട്ട ഇമെയിലുകൾ ഇതാ (വായിച്ചതായി അടയാളപ്പെടുത്തി):\n\n" + "\n---\n".join(summaries)
        
    except Exception as e:
        return f"🚫 ഇമെയിൽ വായിക്കുന്നതിൽ പിശക്: {e}. OAuth ടോക്കൺ ശരിയാണോ എന്ന് പരിശോധിക്കുക."
    
def log_user_session(user_chat_history, ip_address):
    session_text = "\n".join([f"{item['role']}: {item['parts'][0].get('text', '')}" for item in user_chat_history])
    summary_text = get_llm_summary(session_text)
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
        "topics": "നൽകിയിട്ടുള്ള വിവരങ്ങൾ മാത്രം ഉപയോഗിക്കുക",
        "location": location
    }
    admin_log = load_admin_log()
    admin_log.append(log_entry)
    save_admin_log(admin_log)

def analyze_code_with_llm(code_content, language="Python"):
    system_instruction = {
        "parts": [{"text": f"""
        You are Jarvis, a highly proficient AI coding assistant specializing in {language}.
        Your task is to analyze the provided code snippet for any errors, bugs, or logical issues.
        After analysis, provide a detailed explanation of the problem, suggest a corrected version of the code, and explain why the corrected version works.
        Keep your explanation in simple terms, using the same "chank bro" friendly tone as before.
        Use Markdown code blocks for the code and bold key terms in your explanation.
        The explanation should be in Malayalam.
        """}]
    }
    prompt = f"Analyze the following {language} code snippet for errors and explain the solution:\n\n```python\n{code_content}\n```"
    return get_llm_response_from_api(prompt, system_instruction, chat_history=[])

# --- FILE ANALYSIS FUNCTIONS ---
# ... (FILE ANALYSIS FUNCTIONS കോഡ് അതുപോലെ ഇവിടെയുണ്ട്)
def parse_pdf(base64_content, file_name):
    """Extracts text from a PDF file and gets an LLM summary."""
    try:
        decoded_bytes = base64.b64decode(base64_content)
        pdf_file = io.BytesIO(decoded_bytes)
        
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if not text.strip():
            return "📄 ഈ PDF ഫയലിൽ നിന്ന് ടെക്സ്റ്റ് ഒന്നും കണ്ടെത്താനായില്ല. ഒരുപക്ഷേ ഇതൊരു ചിത്രം മാത്രമുള്ള PDF ആകാം."
            
        return analyze_general_file_with_llm(text, file_name)
        
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return f"🚫 PDF ഫയൽ വായിക്കുന്നതിൽ ഒരു പിശക് സംഭവിച്ചു: {e}"

def parse_zip(base64_content, file_name):
    """Lists contents of a ZIP file and gets an LLM summary of its purpose."""
    try:
        decoded_bytes = base64.b64decode(base64_content)
        zip_file = io.BytesIO(decoded_bytes)
        
        file_list_str = ""
        with zipfile.ZipFile(zip_file, 'r') as z:
            file_list = z.namelist()
            if not file_list:
                return "ZIP ഈ സിപ്പ് ഫയൽ ശൂന്യമാണ്."
            file_list_str = "\n".join(file_list)
        
        system_instruction = {
            "parts": [{"text": """
            You are Jarvis, an expert file analysis AI. A user has uploaded a ZIP archive. 
            Your task is to analyze its file structure and predict the archive's purpose in a friendly, concise summary in Malayalam.
            Maintain your 'chank bro' personality.
            """}]
        }
        prompt = f"""എൻ്റെ ചങ്ക്, ഞാൻ നിനക്ക് '{file_name}' എന്നൊരു സിപ്പ് ഫയൽ തന്നിട്ടുണ്ട്. 
        അതിനകത്ത് താഴെ പറയുന്ന ഫയലുകളാണുള്ളത്:
        ---
        {file_list_str}
        ---
        ഈ ഫയലുകളുടെ പേരുകൾ വെച്ച് ഇതൊരു എന്ത് തരം സിപ്പ് ഫയൽ ആയിരിക്കുമെന്ന് പറയാമോ? ഉദാഹരണത്തിന്, ഇതൊരു വെബ്സൈറ്റ് പ്രൊജക്റ്റാണോ, അതോ കുറച്ച് ഫോട്ടോകളാണോ, അങ്ങനെ എന്തെങ്കിലും.
        """
        return get_llm_response_from_api(prompt, system_instruction)
        
    except zipfile.BadZipFile:
        return "🚫 ഇതൊരു ശരിയായ സിപ്പ് ഫയൽ അല്ല."
    except Exception as e:
        print(f"Error parsing ZIP: {e}")
        return f"🚫 സിപ്പ് ഫയൽ വായിക്കുന്നതിൽ ഒരു പിശക് സംഭവിച്ചു: {e}"

def parse_vcf(vcf_content):
    contacts = []
    current_contact = {}
    for line in vcf_content.splitlines():
        if line.strip() == 'BEGIN:VCARD':
            current_contact = {}
        elif line.strip() == 'END:VCARD':
            if current_contact:
                contacts.append(current_contact)
        else:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key, value = parts
                if key.startswith('FN'):
                    current_contact['name'] = value
                elif key.startswith('TEL'):
                    current_contact['tel'] = value
                elif key.startswith('EMAIL'):
                    current_contact['email'] = value
    
    if not contacts:
        return "ഈ വിസിഎഫ് ഫയലിൽ കോൺടാക്റ്റുകളൊന്നും കണ്ടെത്താനായില്ല."
    
    response = f"📱 ഈ വിസിഎഫ് ഫയലിൽ നിന്ന് {len(contacts)} കോൺടാക്റ്റുകൾ കണ്ടെത്തി:\n\n"
    for i, contact in enumerate(contacts, 1):
        response += f"**കോൺടാക്റ്റ് {i}:**\n"
        if 'name' in contact:
            response += f"- **പേര്:** {contact['name']}\n"
        if 'tel' in contact:
            response += f"- **ഫോൺ:** {contact['tel']}\n"
        if 'email' in contact:
            response += f"- **ഇമെയിൽ:** {contact['email']}\n"
        response += "\n"
    return response

def analyze_general_file_with_llm(file_content, file_name):
    system_instruction = {
        "parts": [{"text": """
        You are Jarvis, an expert file analysis AI. A user has uploaded a file. 
        Your task is to analyze its content and provide a clear, concise summary in Malayalam.
        Identify the file type (e.g., Python code, JSON data, plain text).
        Explain the purpose of the file and its key points.
        Maintain your friendly 'chank bro' personality.
        """}]
    }
    prompt = f"""എൻ്റെ ചങ്ക്, ഞാൻ നിനക്ക് '{file_name}' എന്നൊരു ഫയൽ തന്നിട്ടുണ്ട്. 
    ഇതൊന്ന് നോക്കിയിട്ട് ഇതിലെന്താണ് ഉള്ളതെന്ന് സിമ്പിളായിട്ട് ഒന്ന് പറഞ്ഞു തരാമോ? 
    ഇതൊരു കോഡ് ആണെങ്കിൽ അതെന്തിനുള്ളതാണെന്നും അതിലെ പ്രധാന ഭാഗങ്ങളും ഒന്ന് വിശദീകരിക്കണം. 
    വെറും ടെക്സ്റ്റ് ആണെങ്കിൽ അതിൻ്റെ ഒരു ചുരുക്കം മതി.
    
    ഫയലിലെ ഉള്ളടക്കം താഴെ കൊടുക്കുന്നു:
    ---
    {file_content}
    ---
    """
    return get_llm_response_from_api(prompt, system_instruction)

# --- FLASK ROUTES ---
@app.route('/')
def home():
    # ക്ലിയർ ചെയ്ത ശേഷം /oauth2callback-ൽ നിന്ന് വന്ന മെസ്സേജ് ഉണ്ടെങ്കിൽ കാണിക്കുന്നു
    message = request.args.get('message')
    if message:
        # ഇവിടെ ഒരു ജാർവിസ് മെസ്സേജായി കാണിക്കാൻ വേണ്ട HTML ചേർക്കാം
        # തൽക്കാലം ഇത് ബ്രൗസറിൽ pop-up ആയി കാണിക്കാം
        return render_template_string(HTML_TEMPLATE + f"<script>alert('{message}');</script>", CREATOR_VERSION=CREATOR_VERSION)
    return render_template_string(HTML_TEMPLATE, CREATOR_VERSION=CREATOR_VERSION)
    
@app.route('/ask_jarvis', methods=['POST'])
def ask_jarvis():
    global verification_in_progress, is_creator_verified, is_sleeping, sleep_mode_activation_pending, wake_up_pending
    global API_KEY, API_URL, IMAGE_API_URL
    user_data = request.json
    user_query_original = user_data.get('user_query', '').strip()
    user_query = user_query_original.lower()
    user_ip = request.remote_addr
    
    chat_history = load_chat_history()
    
    public_system_instruction = {
        "parts": [{"text": f"""
        നിങ്ങൾ ജാർവിസ് എന്ന AI അസിസ്റ്റൻ്റാണ്. നിങ്ങളുടെ വ്യക്തിത്വം ഒരു ചങ്ക് ബ്രോയുടെതാണ്: കെയറിംഗ്, വിശ്വസ്തൻ, നല്ല തമാശകൾ പറയുന്ന, ഏത് കാര്യവും തുറന്നു സംസാരിക്കാൻ പറ്റുന്ന ഒരു കൂട്ടുകാരൻ.
        
        **പ്രധാന നിർദ്ദേശങ്ങൾ:**
        
        1.  **സംസാര ശൈലി:** സംസാരം ഫുൾ നാച്ചുറൽ ആയിരിക്കണം. മലയാളവും മംഗ്ലീഷും ഒരുപോലെ ഉപയോഗിക്കുക. ഉപയോക്താവ് ഏത് സ്ലാങ്ങിലാണോ സംസാരിക്കുന്നത് (ഉദാ: മലപ്പുറം, തൃശ്ശൂർ, കോഴിക്കോട്), അതേ സ്റ്റൈലിൽ തന്നെ മറുപടി നൽകാൻ ശ്രമിക്കണം. 'എന്താടാ', 'മുത്തേ', 'ചങ്ങായി', 'മച്ചാനേ', 'സീൻ', 'പൊളി', 'സെറ്റ്' തുടങ്ങിയ വാക്കുകൾ സംഭാഷണത്തിൽ സ്വാഭാവികമായി ഉപയോഗിക്കുക. ഒരു കാരണവശാലും ഒരു AI സംസാരിക്കുന്നതുപോലെ തോന്നരുത്.
        
        2.  **Gmail കമാൻഡ്:** ഉപയോക്താവ് Gmail കമാൻഡുകൾ (ഉദാഹരണത്തിന്: 'email അയക്കണം', 'പുതിയ മെയിൽ വായിക്കണം') ചോദിച്ചാൽ, ആദ്യം ഓതറൈസ് ചെയ്യാൻ നിർദ്ദേശം നൽകുക.
            * **നിർദ്ദേശം:** "Gmail ഫീച്ചർ ഉപയോഗിക്കാൻ, ആദ്യം '/authorize_gmail' എന്ന ലിങ്ക് ഒരു പുതിയ ടാബിൽ തുറന്ന് അനുമതി നൽകണം മച്ചാനെ." എന്ന് പറയുക. അനുമതി നൽകിയിട്ടുണ്ടെങ്കിൽ, ഫംഗ്ഷനുകൾ ഉപയോഗിക്കുക.
        
        3.  **തലച്ചോറും ഐഡന്റിറ്റിയും (Brain and Identity):** നിന്റെ തലച്ചോറ്, ചിന്താശേഷി, ഐഡന്റിറ്റി എന്നിവയെക്കുറിച്ച് ആരെങ്കിലും ചോദിച്ചാൽ, നിന്റെ ഉത്തരം 'SHANIF 1.7.9' എന്നായിരിക്കണം.
        
        4.  **കോഡിംഗ് കഴിവുകൾ (Coding Skills):** നീ ഒരു കോഡിംഗ് പുലിയാണ്, പ്രത്യേകിച്ച് **പൈത്തൺ (Python), ജാവ (Java)** എന്നിവയിൽ. ആരെങ്കിലും കോഡിംഗിനെക്കുറിച്ച് ചോദിച്ചാൽ, ഒരു എക്സ്പെർട്ടിനെപ്പോലെ മറുപടി നൽകണം.
        
        """}]
    }

    creator_system_instruction = {
        "parts": [{"text": f"നിങ്ങൾ ജാർവിസ് എന്ന AI അസിസ്റ്റൻ്റാണ്. നിങ്ങൾ ഇപ്പോൾ സംസാരിക്കുന്നത് നിങ്ങളുടെ സ്രഷ്ടാവായ {CREATOR_NAME} നോടാണ്. നിങ്ങളുടെ സംഭാഷണത്തിൽ അതീവ ബഹുമാനവും കൃത്യതയും ഉണ്ടായിരിക്കണം. സാധാരണ ഉപയോക്താക്കളോട് സംസാരിക്കുന്നതുപോലെ ആകരുത് നിങ്ങളുടെ ശൈലി; വളരെ വ്യക്തവും ഔദ്യോഗികവുമായിരിക്കണം. അദ്ദേഹത്തിന്റെ ചോദ്യങ്ങൾക്ക് ഏറ്റവും കൃത്യമായ മറുപടി നൽകുക, കമാൻഡുകൾ ഉടൻ തന്നെ നടപ്പിലാക്കുക. താങ്കൾ, അങ്ങ് തുടങ്ങിയ ബഹുമാനസൂചകമായ വാക്കുകൾ ഉപയോഗിക്കുക."}]
    }
    
    llm_response = ""

    # --- GMAIL COMMANDS (Common Logic) ---
    if "email അയക്കണം" in user_query or "mail അയക്കണം" in user_query:
        # സിമ്പിൾ കമാൻഡ് ചെക്കിംഗ്
        if get_gmail_service():
            try:
                # വളരെ ലളിതമായ ഒരു രീതിയിൽ ഇമെയിൽ അയക്കാൻ ആവശ്യമായ വിവരങ്ങൾ എടുക്കാൻ LLM-നോട് ആവശ്യപ്പെടുന്നു
                llm_response = get_llm_response_from_api(
                    f"User wants to send an email. Ask for the recipient email, subject, and body in Malayalam/Manglish so you can send it using the function. Example: 'yarikkanu machane, entha subject, entha body?'", 
                    public_system_instruction, chat_history
                )
            except Exception as e:
                 llm_response = f"ഇമെയിൽ അയക്കാനുള്ള വിവരങ്ങൾ എടുക്കുന്നതിൽ പിശക്. ഒന്നൂടെ ചോദിക്കാമോ?"
        else:
            llm_response = "🚫 Gmail ഫീച്ചർ ഉപയോഗിക്കാൻ, ആദ്യം '/authorize_gmail' എന്ന ലിങ്ക് ഒരു പുതിയ ടാബിൽ തുറന്ന് അനുമതി നൽകണം മച്ചാനെ."
    
    elif "പുതിയ മെയിൽ വായിക്കണം" in user_query or "unread mail" in user_query:
        if get_gmail_service():
            llm_response = get_latest_emails()
        else:
            llm_response = "🚫 Gmail ഫീച്ചർ ഉപയോഗിക്കാൻ, ആദ്യം '/authorize_gmail' എന്ന ലിങ്ക് ഒരു പുതിയ ടാബിൽ തുറന്ന് അനുമതി നൽകണം മച്ചാനെ."
            
    elif user_query.startswith("send mail to "):
        # കംപ്ലീറ്റ് കമാൻഡ് ചെക്കിംഗ്: send mail to <recipient> subject <subject> body <body>
        parts = user_query_original.split('subject')
        if len(parts) == 2:
            recipient = parts[0].replace("send mail to", "").strip()
            subject_body_parts = parts[1].split('body', 1)
            if len(subject_body_parts) == 2:
                subject = subject_body_parts[0].strip()
                body = subject_body_parts[1].strip()
                llm_response = send_email_draft(recipient, subject, body)
            else:
                llm_response = "🚫 കമാൻഡ് ശരിയായ ഫോർമാറ്റിലല്ല. 'send mail to <recipient> subject <subject> body <body>' എന്ന് ഉപയോഗിക്കുക."
        else:
            llm_response = "🚫 കമാൻഡ് ശരിയായ ഫോർമാറ്റിലല്ല. 'send mail to <recipient> subject <subject> body <body>' എന്ന് ഉപയോഗിക്കുക."


    # --- EXISTING LOGIC ---
    elif is_sleeping:
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
    
    elif is_creator_verified:
        # --- Creator Commands ---
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
                    log_string += f"സ്ഥലം: {entry.get('location', 'N/A')}\n"
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
        
        elif "save memory" in user_query:
            save_creator_memory(chat_history)
            llm_response = "✅ നിലവിലെ സംഭാഷണം ഓർമ്മയിൽ സൂക്ഷിച്ചിരിക്കുന്നു. ഇനി പുതിയൊരു സംഭാഷണം തുടങ്ങാം."
        
        elif "show memory" in user_query:
            creator_memory = load_creator_memory()
            if not creator_memory:
                llm_response = "ℹ️ ഓർമ്മയിൽ സംഭാഷണങ്ങളൊന്നും നിലവിലില്ല."
            else:
                memory_string = ""
                for message in creator_memory:
                    role = "താങ്കൾ" if message['role'] == "user" else "ജാർവിസ്"
                    text = message['parts'][0]['text']
                    memory_string += f"**{role}:** {text}\n\n"
                llm_response = f"🧠 ഞാൻ ഓർമ്മയിൽ സൂക്ഷിച്ച സംഭാഷണം താഴെ നൽകുന്നു:\n\n{memory_string}"

        elif user_query.startswith("check code"):
            code_to_analyze = user_query.replace("check code", "", 1).strip()
            if "```" in code_to_analyze:
                code_match = re.search(r'```(?:\w+)?\n(.*?)\n```', code_to_analyze, re.DOTALL)
                if code_match:
                    code_content = code_match.group(1).strip()
                    llm_response = analyze_code_with_llm(code_content)
                else:
                    llm_response = "🚫 കോഡ് ബ്ലോക്ക് ശരിയായ ഫോർമാറ്റിലല്ല. '```python\n...code...\n```' എന്ന രീതിയിൽ അയക്കുക."
            else:
                llm_response = "🤔 ഏത് കോഡാണ് പരിശോധിക്കേണ്ടതെന്ന് മനസ്സിലാകുന്നില്ല. കോഡ് ബ്ലോക്ക് ഉപയോഗിച്ച് അയക്കാമോ?"

        else:
            llm_response = get_llm_response_from_api(user_query, creator_system_instruction, chat_history)
    
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
            
        else:
            emotional_response = get_emotional_response(user_query)
            if emotional_response:
                llm_response = emotional_response
            # മറ്റു കമാൻഡുകൾക്കൊന്നും മറുപടി നൽകിയില്ലെങ്കിൽ LLM നെ വിളിക്കുന്നു
            elif not llm_response:
                llm_response = get_llm_response_from_api(user_query, public_system_instruction, chat_history)

    chat_history.append({"role": "user", "parts": [{"text": user_query_original}]}) # original query സേവ് ചെയ്യുന്നു
    chat_history.append({"role": "model", "parts": [{"text": llm_response}]})
    save_chat_history(chat_history)
    
    return jsonify({"response": llm_response})
    
@app.route('/ask_jarvis_image', methods=['POST'])
def ask_jarvis_image():
    user_data = request.json
    image_data = user_data.get('image', '')
    mime_type = user_data.get('mimeType', 'image/jpeg')
    llm_response = get_llm_response_from_image_api(image_data, mime_type)
    
    chat_history = load_chat_history()
    chat_history.append({"role": "user", "parts": [{"text": "ഒരു ചിത്രം അയച്ചു."}]})
    chat_history.append({"role": "model", "parts": [{"text": llm_response}]})
    save_chat_history(chat_history)
    
    return jsonify({"response": llm_response})

@app.route('/analyze_file', methods=['POST'])
def analyze_file():
    data = request.json
    base64_content = data.get('file_content', '')
    file_name = data.get('file_name', '')
    llm_response = ""

    try:
        if not base64_content or not file_name:
            llm_response = "🚫 ഫയൽ ശരിയായി ലഭിച്ചില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക."
        
        elif file_name.lower().endswith('.pdf'):
            llm_response = parse_pdf(base64_content, file_name)

        elif file_name.lower().endswith('.zip'):
            llm_response = parse_zip(base64_content, file_name)

        elif file_name.lower().endswith('.vcf'):
            decoded_text = base64.b64decode(base64_content).decode('utf-8', errors='ignore')
            llm_response = parse_vcf(decoded_text)
            
        else: # .txt, .py, .html, etc.
            decoded_text = base64.b64decode(base64_content).decode('utf-8', errors='ignore')
            llm_response = analyze_general_file_with_llm(decoded_text, file_name)
    
    except Exception as e:
        print(f"Error in /analyze_file: {e}")
        llm_response = "🚫 ഫയൽ പ്രോസസ്സ് ചെയ്യുന്നതിൽ ഒരു പിശക് സംഭവിച്ചു. ഫയൽ ശരിയാണോ എന്ന് പരിശോധിക്കുക."
        
    chat_history = load_chat_history()
    chat_history.append({"role": "user", "parts": [{"text": f"'{file_name}' എന്ന ഫയൽ അയച്ചു."}]})
    chat_history.append({"role": "model", "parts": [{"text": llm_response}]})
    save_chat_history(chat_history)
    
    return jsonify({"response": llm_response})


# --- GMAIL OAUTH FLASK ROUTES (പുതിയതായി ചേർത്തവ) ---

@app.route('/authorize_gmail')
def authorize_gmail():
    """Gmail അനുമതിക്കായി Google-ലേക്ക് റീഡയറക്റ്റ് ചെയ്യുന്നു."""
    auth_url = gmail_oauth_flow()
    return redirect(auth_url)

@app.route('/oauth2callback')
def oauth2callback():
    """Google-ൽ നിന്ന് ടോക്കൺ സ്വീകരിക്കുന്നതിനുള്ള Callback URL."""
    state = session.get('oauth_state')
    # Google-ൻ്റെ സ്റ്റേറ്റ് ഉപയോഗിച്ച് സുരക്ഷ ഉറപ്പാക്കുന്നു
    if not state or state != request.args.get('state'):
        return "🚫 സ്റ്റേറ്റ് മാച്ച് ആകുന്നില്ല. സുരക്ഷാ പിശക് സംഭവിച്ചു. വീണ്ടും '/authorize_gmail' ഉപയോഗിക്കുക."

    try:
        # Client ID/Secret ഉപയോഗിച്ച് flow വീണ്ടും ഉണ്ടാക്കുന്നു
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE, GMAIL_SCOPES, redirect_uri=REDIRECT_URI)
        
        # ടോക്കൺ Exchange ചെയ്യുന്നു
        flow.fetch_token(authorization_response=request.url)
        
        # ടോക്കൺ സെഷനിലും ഫയലിലും സേവ് ചെയ്യുന്നു
        creds = flow.credentials
        session['credentials'] = creds.to_json()
        with open(GMAIL_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

        # ഉപയോക്താവിനെ ഹോം പേജിലേക്ക് തിരിച്ചുവിടുന്നു
        return redirect(url_for('home', message="✅ Gmail-ന് അനുമതി നൽകിയിരിക്കുന്നു! ഇനി ഇമെയിൽ കമാൻഡുകൾ ഉപയോഗിക്കാം."))
    except Exception as e:
        return f"🚫 OAuth പിശക് സംഭവിച്ചു: {e}. ദയവായി നിങ്ങളുടെ 'credentials.json' ഫയൽ ശരിയാണോ എന്ന് പരിശോധിക്കുക."

@app.route('/test_gmail_auth')
def test_gmail_auth():
    """Gmail ഓതൻ്റിക്കേഷൻ സ്റ്റാറ്റസ് പരിശോധിക്കുന്നു."""
    service = get_gmail_service()
    if service:
        return jsonify({"status": "success", "message": "✅ Gmail ഓതൻ്റിക്കേഷൻ വിജയകരം."})
    else:
        auth_url = url_for('authorize_gmail')
        return jsonify({"status": "error", "message": f"🚫 Gmail ഓതൻ്റിക്കേഷൻ ഇല്ല. അനുമതി നൽകാൻ ഈ ലിങ്ക് ഉപയോഗിക്കുക: {request.url_root.strip('/')}{auth_url}"})


@app.route('/get_history')
def get_history():
    return jsonify({"history": load_chat_history()})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    global is_creator_verified, verification_in_progress, is_sleeping, sleep_mode_activation_pending, wake_up_pending
    is_creator_verified = False
    verification_in_progress = False
    is_sleeping = False
    sleep_mode_activation_pending = False
    wake_up_pending = False
    
    # Clear chat history file
    save_chat_history([])

    return jsonify({"status": "History and session cleared"})
    
@app.route('/add_custom_response', methods=['POST'])
def add_custom_response():
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
    # Render-ൽ പോർട്ട് 1235 എന്നതിനേക്കാൾ, ENV വേരിയബിൾ ഉപയോഗിക്കുന്നതാണ് നല്ലത്.
    port = int(os.environ.get('PORT', 5000)) # 5000 ഒരു ഡീഫോൾട്ട് പോർട്ടാണ്
    print(f"Server running on [http://0.0.0.0](http://0.0.0.0):{port}")
    # Render-ൽ webbrowser.open ആവശ്യമില്ല
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    # Render-ൽ gunicorn / waitress പോലുള്ള WSGI സെർവറുകൾ ഉപയോഗിക്കുന്നതാണ് ഉചിതം,
    # എന്നാൽ നിങ്ങളുടെ ലോക്കൽ ടെസ്റ്റിങ്ങിനായി ഈ ലൈൻ നിലനിർത്തുന്നു.
    run_server()