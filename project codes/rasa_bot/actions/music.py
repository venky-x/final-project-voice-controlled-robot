import subprocess
import threading
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
import time

# Global Flags
music_process = None
is_music_playing = False  
music_timer = None  

class ActionPlayMusic(Action):
    def name(self) -> str:
        return "action_play_music"
    
    def run(self, dispatcher: CollectingDispatcher, tracker, domain) -> list:
        global music_process, is_music_playing, music_timer
        music_url = "http://stream.radioparadise.com/mp3-192"
        MUSIC_DURATION = 20.0  
        VOLUME_LEVEL = 30  

        # Kill any existing music and timer before playing new one
        if music_process:
            music_process.terminate()
        if music_timer:
            music_timer.cancel()

        # Start music 
        try:
            music_process = subprocess.Popen(["mpg123", "-g", str(VOLUME_LEVEL), music_url])
            is_music_playing = True  # Set flag to True when music starts
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I couldn’t play the music: {str(e)}")
            return []

        # function to stop the music after the timer
        def stop_music():
            global music_process, is_music_playing, music_timer
            if music_process:
                music_process.terminate()
                music_process = None
            is_music_playing = False  
            music_timer = None
            time.sleep(1)
            dispatcher.utter_message(text="Music has finished playing.")


        music_timer = threading.Timer(MUSIC_DURATION, stop_music)
        music_timer.start()
        return []

class ActionStopMusic(Action):
    def name(self) -> str:
        return "action_stop_music"
    
    def run(self, dispatcher: CollectingDispatcher, tracker, domain) -> list:
        global music_process, is_music_playing, music_timer
        if music_process:
            music_process.terminate()
            music_process = None
            if music_timer:
                music_timer.cancel()  
                music_timer = None
            is_music_playing = False  
            time.sleep(1)
            dispatcher.utter_message(text="Music stopped!")
        else:
            dispatcher.utter_message(text="No music is currently playing.")
        return []
