import subprocess
import threading
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
import time

# global Flags
news_process = None
is_news_playing = False  

class ActionPlayNews(Action):
    def name(self) -> str:
        return "action_play_news"
    
    def run(self, dispatcher: CollectingDispatcher, tracker, domain) -> list:
        global news_process, is_news_playing
        news_url = "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"
        VOLUME_LEVEL = 70  
        NEWS_DURATION = 20.0  

        # Stop previous process if already playing
        if news_process:
            news_process.terminate()

        # Start news stream 
        try:
            news_process = subprocess.Popen(["mpg123", "-g", str(VOLUME_LEVEL), news_url])
            is_news_playing = True  
            dispatcher.utter_message(text=f"Now playing the latest news at {VOLUME_LEVEL}% volume!")
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I couldn’t play the news: {str(e)}")
            return []

        # function to stop the news after the timer
        def stop_news():
            global news_process, is_news_playing
            if news_process:
                news_process.terminate()
                news_process = None
            is_news_playing = False  
            time.sleep(1)
            dispatcher.utter_message(text="News has finished playing.")

        threading.Timer(NEWS_DURATION, stop_news).start()
        return []

class ActionStopNews(Action):
    def name(self) -> str:
        return "action_stop_news"
    
    def run(self, dispatcher: CollectingDispatcher, tracker, domain) -> list:
        global news_process, is_news_playing
        if news_process:
            news_process.terminate()
            news_process = None
            is_news_playing = False  
            time.sleep(1)
            dispatcher.utter_message(text="News stopped!")
        else:
            dispatcher.utter_message(text="No news is currently playing.")
        return []
