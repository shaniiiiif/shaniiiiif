import datetime
import sys
import requests
import json
import time
import os
import re
import threading
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for 
import base64
import io

# Gmail ഫീച്ചർ തൽക്കാലം വർക്ക് ആയില്ലെങ്കിലും എറർ വരാതിരിക്കാൻ ഇത് സഹായിക്കും
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("Google libraries not found, Gmail features will be disabled")
	

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
CLIENT_SECRET_FILE = 'credentials.json' 
REDIRECT_URI =  'https://shaniiiiif-7.onrender.com/oauth2callback' 


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
    return "AIzaSyDYaOVzYtIgr9tY8tejDyI0_tECC9Tt8vU" 

def save_api_key(key):
    """Saves API key to a JSON file."""
    with open(API_KEY_FILE, 'w', encoding='utf-8') as f:
        json.dump({"api_key": key}, f, ensure_ascii=False, indent=4)

# Load the API key at startup
API_KEY = load_api_key()

# --- FIXED MODEL LINKS ---
# 'gemini-2.5' എന്നത് മാറ്റി 'gemini-1.5-flash' ആക്കി
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
IMAGE_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
TTS_API_URL = API_URL 

app = Flask(__name__)
app.secret_key = 'shanif_secret_jarvis_123'

# Global variables
is_creator_verified = False
verification_in_progress = False
is_sleeping = False
sleep_mode_activation_pending = False
wake_up_pending = False

CREATOR_NAME = "SHANIF P"
CREATOR_VERSION = "1.7.9"

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
    "തുടരുക": "➡️", "തിриകെ": "🔙", "മരണപെട്ടു": "💀", "മരണം": "💀", "പുതിയത്": "✨",
    "pdf": "📄", "zip": "ZIP"
}

# HTML Template remains same as your original
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
    // JS Logic stays the same
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
            chatWindow.innerHTML = ''; 
            if (data.history) {
                data.history.forEach(item => {
                    const role = item.role === 'user' ? 'user' : 'jarvis';
                    if (item.parts && item.parts[0] && item.parts[0].text) {
                       createMessageElement(item.parts[0].text, role);
                    }
                });
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }
    
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
def get_location_from_query(query):
    locations = ["കൊച്ചി", "കേരളം", "ഇന്ത്യ", "തിരുവനന്തപുരം", "കോഴിക്കോട്", "london", "new york", "paris"]
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

def load_custom_responses(): return load_json_file(CUSTOM_RESPONSES_FILE, {})
def save_custom_responses(responses): save_json_file(CUSTOM_RESPONSES_FILE, responses)
def load_chat_history(): return load_json_file(CHAT_HISTORY_FILE, [])
def save_chat_history(history): save_json_file(CHAT_HISTORY_FILE, history)
def load_creator_memory(): return load_json_file(CREATOR_MEMORY_FILE, [])
def save_creator_memory(history): save_json_file(CREATOR_MEMORY_FILE, history)
def load_admin_log(): return load_json_file(ADMIN_LOG_FILE, [])
def save_admin_log(log): save_json_file(ADMIN_LOG_FILE, log)
def load_admin_data(): return load_json_file(ADMIN_DATA_FILE, {"creator": CREATOR_NAME})
def save_admin_data(data): save_json_file(ADMIN_DATA_FILE, data)

def get_emotional_response(user_query):
    sad_keywords = ["വിഷമമുണ്ട്", "സങ്കടം", "വിഷമം", "സന്തോഷമില്ല", "ഒറ്റപ്പെട്ടു", "ഒറ്റയ്ക്ക്", "ദുഃഖം", "പ്രശ്നം"]
    angry_keywords = ["ദേഷ്യം", "ദേഷ്യമുണ്ട്", "ദേഷ്യത്തിലാണ്", "എനിക്ക് ഇഷ്ടമല്ല", "സഹിക്കുന്നില്ല"]
    happy_keywords = ["സന്തോഷം", "സന്തോഷമുണ്ട്", "സന്തോഷത്തിലാണ്", "ഹാപ്പി", "സന്തോഷിച്ചു", "സന്തോഷമായി"]
    for keyword in sad_keywords:
        if keyword in user_query: return "😔 നിങ്ങൾക്ക് വിഷമമുണ്ടെന്ന് മനസ്സിലാക്കുന്നു. വിഷമിക്കേണ്ട, ഞാൻ ഇവിടെയുണ്ട്."
    for keyword in angry_keywords:
        if keyword in user_query: return "😡 നിങ്ങൾ ദേഷ്യത്തിലാണെന്ന് തോന്നുന്നു. ഒരു ദീർഘ ശ്വാസമെടുക്കൂ."
    for keyword in happy_keywords:
        if keyword in user_query: return "😊 നിങ്ങൾ സന്തോഷത്തിലാണെന്ന് കേട്ടതിൽ എനിക്കും സന്തോഷമുണ്ട്!"
    return None

# --- CORE LLM FUNCTIONS ---
def get_llm_response_from_api(prompt, system_instruction, chat_history=None, retries=3):
    if chat_history is None: chat_history = []
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
            if not result.get('candidates'): return "ക്ഷമിക്കണം, എനിക്ക് ഇപ്പോൾ ഒരു പ്രതികരണം നൽകാൻ കഴിയില്ല."
            candidate = result.get('candidates', [])[0]
            if 'content' in candidate and 'parts' in candidate['content']:
                text = candidate['content']['parts'][0]['text']
                emoji = find_appropriate_emoji(text)
                return f"{emoji} {text}" if emoji else text
        except Exception:
            if i < retries - 1: time.sleep(2)
    return "എനിക്കിപ്പോൾ മറുപടി തരാൻ സാധിക്കുന്നില്ല. പിന്നീട് ശ്രമിക്കാമോ?"

def get_llm_response_from_image_api(image_data, mime_type, retries=3):
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": "Analyze image in Malayalam."}, {"inlineData": {"mimeType": mime_type, "data": image_data}}]}]}
    for i in range(retries):
        try:
            response = requests.post(IMAGE_API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            text = result.get('candidates', [])[0]['content']['parts'][0]['text']
            return text
        except Exception:
            if i < retries - 1: time.sleep(2)
    return "ചിത്രം വിശകലനം ചെയ്യാൻ സാധിക്കുന്നില്ല."

# --- GMAIL & OTHER FUNCTIONS ---
def get_gmail_service():
    if 'credentials' in session:
        creds = Credentials.from_authorized_user_info(json.loads(session['credentials']), GMAIL_SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            session['credentials'] = creds.to_json()
        return build('gmail', 'v1', credentials=creds)
    return None

def gmail_oauth_flow():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, GMAIL_SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['oauth_state'] = state
    return auth_url

# --- FILE ANALYZERS ---
def parse_pdf(base64_content, file_name):
    try:
        decoded_bytes = base64.b64decode(base64_content)
        pdf_file = io.BytesIO(decoded_bytes)
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages: text += (page.extract_text() or "") + "\n"
        return analyze_general_file_with_llm(text, file_name)
    except Exception as e: return f"🚫 PDF Error: {e}"

def analyze_general_file_with_llm(file_content, file_name):
    system_instruction = {"parts": [{"text": "You are Jarvis, summarize this file in Malayalam."}]}
    prompt = f"File Name: {file_name}\nContent: {file_content[:2000]}"
    return get_llm_response_from_api(prompt, system_instruction)

# --- FLASK ROUTES ---
@app.route('/')
def home():
    message = request.args.get('message')
    return render_template_string(HTML_TEMPLATE + (f"<script>alert('{message}');</script>" if message else ""), CREATOR_VERSION=CREATOR_VERSION)

@app.route('/ask_jarvis', methods=['POST'])
def ask_jarvis():
    global verification_in_progress, is_creator_verified, is_sleeping, wake_up_pending
    global API_KEY, API_URL, IMAGE_API_URL
    user_data = request.json
    user_query_original = user_data.get('user_query', '').strip()
    user_query = user_query_original.lower()
    chat_history = load_chat_history()
    
    public_system_instruction = {"parts": [{"text": "നിങ്ങൾ ജാർവിസ് എന്ന AI അസിസ്റ്റൻ്റാണ്. ചങ്ക് ബ്രോ സ്റ്റൈലിൽ സംസാരിക്കുക."}]}
    creator_system_instruction = {"parts": [{"text": f"നിങ്ങൾ നിങ്ങളുടെ സ്രഷ്ടാവായ {CREATOR_NAME} നോട് ബഹുമാനത്തോടെ സംസാരിക്കുന്നു."}]}
    
    llm_response = ""

    # Reset API URL logic inside command
    if user_query.startswith("change api key"):
        parts = user_query.split()
        if len(parts) >= 4:
            new_key = parts[3]
            save_api_key(new_key)
            API_KEY = new_key
            # FIXED: Correct Gemini 1.5 link used here
            API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            IMAGE_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            llm_response = "✅ API കീ വിജയകരമായി അപ്ഡേറ്റ് ചെയ്തിരിക്കുന്നു മച്ചാനേ."
        else:
            llm_response = "🚫 ഫോർമാറ്റ്: 'change api key <key>'"
    
    elif "wake up" in user_query:
        wake_up_pending = True
        llm_response = "❓ താങ്കളുടെ ഐഡന്റിറ്റി സ്ഥിരീകരിക്കാനായി ഒരു ചോദ്യത്തിന് ഉത്തരം നൽകുക. ആരാണ് കാർലോ?"
    
    elif wake_up_pending:
        if user_query == "carloe":
            is_creator_verified = True; is_sleeping = False; wake_up_pending = False
            llm_response = "😊 സ്വാഗതം സ്രഷ്ടാവേ, ഞാൻ ഇപ്പോൾ റെഡിയാണ്."
        else:
            wake_up_pending = False; llm_response = "🚫 ഐഡന്റിറ്റി തെറ്റാണ്."

    elif is_sleeping:
        llm_response = "💤 ഞാൻ സ്ലീപ്പ് മോഡിലാണ്. 'wake up' എന്ന് പറയുക."

    else:
        # Check for creator questions
        if "creator" in user_query or "സ്രഷ്ടാവ്" in user_query:
            llm_response = f"👨‍💻 എൻ്റെ സ്രഷ്ടാവ് {CREATOR_NAME} ആണ്. ഷാനിഫ് വേങ്ങര സ്വദേശിയാണ്."
        elif "i am your creator" in user_query:
            verification_in_progress = True
            llm_response = "❓ ആരാണ് കാർലോ?"
        elif verification_in_progress:
            if user_query == "carloe":
                is_creator_verified = True; verification_in_progress = False
                llm_response = "✅ വെരിഫൈഡ്!"
            else:
                verification_in_progress = False; llm_response = "❌ തെറ്റാണ്."
        else:
            # Standard AI response
            system_instr = creator_system_instruction if is_creator_verified else public_system_instruction
            llm_response = get_llm_response_from_api(user_query, system_instr, chat_history)

    chat_history.append({"role": "user", "parts": [{"text": user_query_original}]})
    chat_history.append({"role": "model", "parts": [{"text": llm_response}]})
    save_chat_history(chat_history)
    return jsonify({"response": llm_response})

@app.route('/oauth2callback')
def oauth2callback():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, GMAIL_SCOPES, redirect_uri=REDIRECT_URI)
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session['credentials'] = creds.to_json()
    with open(GMAIL_TOKEN_FILE, 'w') as token: token.write(creds.to_json())
    return redirect(url_for('home', message="✅ Gmail റെഡിയായി മച്ചാനേ!"))

@app.route('/get_history')
def get_history(): return jsonify({"history": load_chat_history()})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    save_chat_history([])
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
