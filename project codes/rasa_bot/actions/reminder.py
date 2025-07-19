from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import json
import datetime
import requests
import time
import threading
import os

REMINDER_FILE = os.path.join(os.path.dirname(__file__), "reminders.json")
TELEGRAM_TOKEN = "YOUR TELEGRAM TOKEN"
CHAT_ID = "YOUR CHAT ID"

# Function to send a message to Telegram
def send_telegram(chat_id, message):
    response = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        params={"chat_id": chat_id, "text": message}
    )
    if response.status_code != 200:
        print(f"Failed to send message to Telegram: {response.text}")

# Scheduler function to check reminders and send them at the right time
def run_scheduler():
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        try:
            with open(REMINDER_FILE, "r") as f:
                reminders = json.load(f)
        except FileNotFoundError:
            reminders = []

        updated = False
        for r in reminders:
            if r.get("sent", False):  # Skip if already sent
                continue
            if r["time"] == now:
                send_telegram(r["chat_id"], f"Reminder: {r['task']}")
                r["sent"] = True  # Mark as sent
                updated = True

        if updated:
            with open(REMINDER_FILE, "w") as f:
                json.dump(reminders, f, indent=4)

        time.sleep(60)

# Start the scheduler in a background thread when the action server starts
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

class ActionSetReminder(Action):
    def name(self):
        return "action_set_reminder"

    def run(self, dispatcher, tracker, domain):
        task = tracker.get_slot("task")
        time_str = tracker.get_slot("time")

        # Debugging: Log the extracted slots
        print(f"Extracted task: {task}")
        print(f"Extracted time: {time_str}")

        # Check if slots are filled
        if not task or not time_str:
            dispatcher.utter_message(text="I couldn't understand the task or time. Please try again.")
            return []

        # Save to reminders.json
        try:
            with open(REMINDER_FILE, "r") as f:
                reminders = json.load(f)
        except FileNotFoundError:
            reminders = []

        reminders.append({
            "task": task,
            "time": time_str,
            "chat_id": CHAT_ID,
            "sent": False  # Initialize sent flag
        })

        with open(REMINDER_FILE, "w") as f:
            json.dump(reminders, f, indent=4)

        # Send confirmation to Telegram
        message = f" Reminder set: {task} at {time_str}"
        send_telegram(CHAT_ID, message)

        dispatcher.utter_message(text=message)
        return [SlotSet("task", None), SlotSet("time", None)]
