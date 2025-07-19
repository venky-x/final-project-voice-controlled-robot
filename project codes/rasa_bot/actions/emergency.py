from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
import json
import requests
import datetime
import os

EMERGENCY_FILE = os.path.join(os.path.dirname(__file__), "emergency.json")
TELEGRAM_TOKEN = "YOUR TELEGRAM TOKEN"
CHAT_ID = "YOUR TELEGRAM CHAT ID"

# Function to send a message to Telegram
def send_telegram(chat_id, message):
    response = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        params={"chat_id": chat_id, "text": message}
    )
    if response.status_code != 200:
        print(f"Failed to send message to Telegram: {response.text}")

# Function to save emergency request to emergency.json
def save_emergency(chat_id, message):
    emergency = {
        "chat_id": chat_id,
        "message": message,
        "timestamp": datetime.datetime.now().isoformat()
    }
    try:
        with open(EMERGENCY_FILE, "r") as f:
            emergencies = json.load(f)
    except FileNotFoundError:
        emergencies = []

    emergencies.append(emergency)

    with open(EMERGENCY_FILE, "w") as f:
        json.dump(emergencies, f, indent=4)

class ActionSendEmergency(Action):
    def name(self):
        return "action_send_emergency"

    def run(self, dispatcher, tracker, domain):
        # Send emergency message to Telegram
        emergency_message = "emergency! help needed"
        send_telegram(CHAT_ID, emergency_message)

        # Save to emergency.json
        save_emergency(CHAT_ID, emergency_message)

        # Respond to user in chat
        dispatcher.utter_message(text="Help is on the way! An emergency message has been sent.")
        return []
