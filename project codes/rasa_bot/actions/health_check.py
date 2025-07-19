from rasa_sdk import Action
from rasa_sdk.events import SlotSet, UserUttered, FollowupAction
import time

class ActionGoodbye(Action):
    def name(self) -> str:
        return "action_goodbye"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Goodbye! Take care.")
        return []

class ActionHealthResponse(Action):
    def name(self) -> str:
        return "action_health_response"

    def run(self, dispatcher, tracker, domain):
        health_status = tracker.get_slot("health_status")
        if not health_status:  
            health_response = "Sorry, I didn’t understand your health status."
            dispatcher.utter_message(response="utter_health_response", health_response=health_response)
            return []

        health_status = health_status.lower()

        # Define emotional keyword groups
        good_terms = ["good", "happy", "very happy", "okay", "fine", "great"]
        tired_terms = ["tired", "very tired", "exhausted", "worn out"]
        unwell_terms = [
            "unwell", "sick", "ill", "bad", "not feeling well", "not feeling good",
            "not well", "under the weather", "poorly", "not feeling great", "very unwell"
        ]
        sad_terms = ["sad", "depressed", "very sad", "down", "blue", "low", "unmotivated"]
        angry_terms = ["angry", "mad", "furious", "annoyed", "irritated", "frustrated"]

        # Respond based on detected emotion
        if any(term in health_status for term in good_terms):
            health_response = "I’m glad you’re feeling good!"
        elif any(term in health_status for term in tired_terms):
            health_response = "Sounds like you've had a long day. Make sure to get some rest."
        elif any(term in health_status for term in sad_terms):
            health_response = "I’m sorry you’re feeling sad. Remember, you're not alone. I'm here to talk."
        elif any(term in health_status for term in angry_terms):
            health_response = "It’s okay to feel angry sometimes. Take a deep breath. I'm here if you need to vent."
        elif any(term in health_status for term in unwell_terms):
            health_response = "I’m sorry you’re feeling unwell. Please take care."

        else:
            health_response = "Thanks for sharing. I'm here if you want to talk more."

        dispatcher.utter_message(response="utter_health_response", health_response=health_response)
        return []
