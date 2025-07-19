from datetime import datetime
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher

class ActionTime(Action):
    def name(self):
        return "action_time"

    def run(self, dispatcher, tracker, domain):
        now = datetime.now().strftime("%H:%M")
        dispatcher.utter_message(text=f"The current time is {now}.")
        return []

class ActionDate(Action):
    def name(self):
        return "action_date"

    def run(self, dispatcher, tracker, domain):
        today = datetime.now().strftime("%A, %d %B %Y")
        dispatcher.utter_message(text=f"Today's date is {today}.")
        return []

