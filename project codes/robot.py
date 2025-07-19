import cv2
import threading
import time
import RPi.GPIO as GPIO
from pynput import keyboard
import queue as sd_queue
import json
import os
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import mediapipe as mp
import face_recognition
import sys
import termios
import tty
import requests

# Global Flags
gesture_mode_active = False
system_running = True
audio_stream = None
latest_frame = None
frame_lock = threading.Lock()
gpio_lock = threading.Lock()
keyboard_listener = None
camera_feed_open = False
mic_muted = False
threads = []  

# Motor controls config
AI1, AI2, PWMA = 23, 24, 19
BI1, BI2, PWMB = 27, 17, 18
CI1, CI2, PWMC = 5, 6, 12
DI1, DI2, PWMD = 22, 26, 13
STBY_1, STBY_2 = 25, 16
pwm_a, pwm_b, pwm_c, pwm_d = None, None, None, None

# Password attempts
PASSWORD = "robot"
MAX_FACE_ATTEMPTS = 3
MAX_PASSWORD_ATTEMPTS = 3

# Rasa config
RASA_URL = "http://localhost:5005/webhooks/rest/webhook"

# Function to Clear Keyboard buffer
def clear_keyboard_buffer():
    try:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            termios.tcflush(fd, termios.TCIFLUSH)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception as e:
        print(f"Error clearing keyboard buffer: {e}")

# GPIO Setup 
def setup_gpio():
    global pwm_a, pwm_b, pwm_c, pwm_d
    with gpio_lock:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        motor_pins = [AI1, AI2, PWMA, BI1, BI2, PWMB, CI1, CI2, PWMC, DI1, DI2, PWMD, STBY_1, STBY_2]
        for pin in motor_pins:
            GPIO.setup(pin, GPIO.OUT)

        GPIO.output(STBY_1, GPIO.HIGH)
        GPIO.output(STBY_2, GPIO.HIGH)

        pwm_a = GPIO.PWM(PWMA, 1000)
        pwm_b = GPIO.PWM(PWMB, 1000)
        pwm_c = GPIO.PWM(PWMC, 1000)
        pwm_d = GPIO.PWM(PWMD, 1000)

        for pwm in [pwm_a, pwm_b, pwm_c, pwm_d]:
            pwm.start(0)

# Motor controls
def set_motors(a1, a2, b1, b2, c1, c2, d1, d2, speed):
    with gpio_lock:
        if not GPIO.getmode():
            print("GPIO error")
            setup_gpio()
        try:
            GPIO.output(AI1, a1)
            GPIO.output(AI2, a2)
            GPIO.output(BI1, b1)
            GPIO.output(BI2, b2)
            GPIO.output(CI1, c1)
            GPIO.output(CI2, c2)
            GPIO.output(DI1, d1)
            GPIO.output(DI2, d2)
            for pwm in [pwm_a, pwm_b, pwm_c, pwm_d]:
                if pwm is not None:
                    pwm.ChangeDutyCycle(speed)
                else:
                    print("PWM error ")
        except Exception as e:
            print(f"Error in set_motors: {e}")

def move_forward(speed): set_motors(1, 0, 1, 0, 1, 0, 1, 0, speed)
def move_backward(speed): set_motors(0, 1, 0, 1, 0, 1, 0, 1, speed)
def move_left(speed): set_motors(0, 1, 1, 0, 0, 1, 1, 0, speed)
def move_right(speed): set_motors(1, 0, 0, 1, 1, 0, 0, 1, speed)
def move_diagonalright_forward(speed): set_motors(1, 0, 0, 0, 1, 0, 0, 0, speed)
def move_diagonalleft_forward(speed): set_motors(0, 0, 1, 0, 0, 0, 1, 0, speed)
def move_diagonalright_backward(speed): set_motors(0, 0, 0, 1, 0, 0, 0, 1, speed)
def move_diagonalleft_backward(speed): set_motors(0, 1, 0, 0, 0, 1, 0, 0, speed)
def turn_right(speed): set_motors(0, 1, 0, 1, 1, 0, 1, 0, speed)
def turn_left(speed): set_motors(1, 0, 1, 0, 0, 1, 0, 1, speed)
def stop_motors():
    with gpio_lock:
        try:
            for pwm in [pwm_a, pwm_b, pwm_c, pwm_d]:
                if pwm is not None:
                    pwm.ChangeDutyCycle(0)
                else:
                    print("PWM error")
        except Exception as e:
            print(f"Error in stop_motors: {e}")

# Text-to-Speech (vosk)
def speak(text):
    global audio_stream, mic_muted
    if audio_stream and audio_stream.active:
        audio_stream.stop()
        mic_muted = True
    os.system(f'espeak-ng -v en+m3 -p 90 -s 150 "{text}"')
    if audio_stream and not audio_stream.active:
        audio_stream.start()
    mic_muted = False

# Keyboard Control 
def on_press(key):
    global gesture_mode_active, camera_feed_open, system_running, audio_stream, keyboard_listener, threads
    try:
        if hasattr(key, 'char') and system_running:
            k = key.char
            if k == 'c':
                print("Shutting down via key press...")
                speak("Shutting down")
                stop_motors()
                system_running = False
                if audio_stream:
                    audio_stream.stop()
                    audio_stream.close()
                if keyboard_listener:
                    keyboard_listener.stop()
                time.sleep(0.1)
                current_thread = threading.current_thread()
                for thread in threads[:]:
                    if thread != current_thread and thread.is_alive():
                        thread.join(timeout=1)
                if camera_feed_open:
                    cv2.destroyWindow("Gesture Mode")
                cv2.destroyAllWindows()
                GPIO.cleanup()
                clear_keyboard_buffer()
                sys.exit(0)
            elif k == 'q':
                print("Forward")
                speak("moving forward")
                move_forward(50)
            elif k == 'w':
                print("Backward")
                speak("moving backward")
                move_backward(50)
            elif k == 'e':
                print("Left")
                speak("moving left")
                move_left(50)
            elif k == 'r':
                print("Right")
                speak("moving right")
                move_right(50)
            elif k == 't':
                print("Diag L-F")
                speak("moving diagonally left forward")
                move_diagonalleft_forward(50)
            elif k == 'y':
                print("Diag R-F")
                speak("moving diagonally right forward")
                move_diagonalright_forward(50)
            elif k == 'u':
                print("Diag R-B")
                speak("moving diagonally right backward")
                move_diagonalright_backward(50)
            elif k == 'i':
                print("Diag L-B")
                speak("moving diagonally left backward")
                move_diagonalleft_backward(50)
            elif k == 'o':
                print("Turn R")
                speak("turning right")
                turn_right(50)
            elif k == 'p':
                print("Turn L")
                speak("turning left")
                turn_left(50)
            elif k == 'a':
                print("Stop")
                speak("stopping motors")
                stop_motors()
            elif k == 'g':
                gesture_mode_active = not gesture_mode_active
                print(f"[Control] Gesture mode {'ON' if gesture_mode_active else 'OFF'}")
                speak(f"Gesture mode {'activated' if gesture_mode_active else 'deactivated'}")
                if not gesture_mode_active and camera_feed_open:
                    cv2.destroyWindow("Gesture Mode")
                    camera_feed_open = False
    except Exception as e:
        print(f"Error in on_press: {e}")

def start_keyboard_listener():
    global keyboard_listener, threads
    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.start()
    threads.append(threading.Thread(target=keyboard_listener.join, daemon=True))
    threads[-1].start()

# Gesture Control 
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

def get_hand_box(landmarks, shape):
    x_min = min([lm.x for lm in landmarks])
    x_max = max([lm.x for lm in landmarks])
    y_min = min([lm.y for lm in landmarks])
    y_max = max([lm.y for lm in landmarks])
    return int(x_min * shape[1]), int(y_min * shape[0]), int(x_max * shape[1]), int(y_max * shape[0])

def gesture_mode():
    global gesture_mode_active, system_running, latest_frame
    try:
        while system_running:
            if gesture_mode_active:
                with frame_lock:
                    if latest_frame is None:
                        time.sleep(0.1)
                        continue
                    frame = latest_frame.copy()
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(frame_rgb)

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        x_min, y_min, x_max, y_max = get_hand_box(hand_landmarks.landmark, frame.shape)
                        width = x_max - x_min
                        height = y_max - y_min
                        center_x = (x_min + x_max) // 2
                        frame_center_x = frame.shape[1] // 2
                        threshold = 110

                        if center_x < frame_center_x - threshold:
                            print("Move Left")
                            speak("Moving left")
                            move_left(50)
                        elif center_x > frame_center_x + threshold:
                            print("Move Right")
                            speak("Moving right")
                            move_right(50)
                        else:
                            if width > 200 and height > 200:
                                print("Move Backward")
                                speak("moving backward")
                                move_backward(50)
                            elif width <= 500 and height <= 500:
                                print("Move Forward")
                                speak("moving forward")
                                move_forward(50)
                else:
                    stop_motors()
            else:
                time.sleep(0.1)
    except Exception as e:
        print(f"Gesture mode error: {e}")
    finally:
        stop_motors()
        
# Start Gesture Thread
def start_gesture():
    global threads
    thread = threading.Thread(target=gesture_mode, daemon=True)
    thread.start()
    threads.append(thread)
    
# Voice password unlock
def voice_password_input():
    global audio_stream, system_running, mic_muted
    model_path = "/home/venki/robot_project/vosk-model-small-en-us-0.15"
    model = Model(model_path)
    rec = KaldiRecognizer(model, 16000)
    q = sd_queue.Queue()

    def callback(indata, frames, time, status):
        if not mic_muted:
            q.put(bytes(indata))

    audio_stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                     channels=1, callback=callback)
    audio_stream.start()

    while not q.empty():
        try:
            q.get_nowait()
        except sd_queue.Empty:
            break

    for attempt in range(1, MAX_PASSWORD_ATTEMPTS + 1):
        speak(f"Face recognition failed three times. Attempt {attempt} of {MAX_PASSWORD_ATTEMPTS}. Please say the password.")

        while not q.empty():
            try:
                q.get_nowait()
            except sd_queue.Empty:
                break

        timeout = 10
        start_time = time.time()

        while system_running and (time.time() - start_time < timeout):
            try:
                data = q.get(timeout=1)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").lower().replace(" ", "")
                    print("Heard password:", text)
                    if text == PASSWORD:
                        speak("Access granted")
                        return True
                    else:
                        if attempt < MAX_PASSWORD_ATTEMPTS:
                            speak(f"Incorrect password. Attempt {attempt + 1} of {MAX_PASSWORD_ATTEMPTS}.")
                            while not q.empty():
                                try:
                                    q.get_nowait()
                                except sd_queue.Empty:
                                    break
                        break
                time.sleep(0.1)
            except sd_queue.Empty:
                continue

    speak("All password attempts failed. Access denied.")
    while not q.empty():
        try:
            q.get_nowait()
        except sd_queue.Empty:
            break
    return False

# face verification
def face_verification():
    global system_running, latest_frame, audio_stream, mic_muted
    known_face = face_recognition.load_image_file("/home/venki/robot_project/known_faces/venki.jpg")
    known_encoding = face_recognition.face_encodings(known_face)[0]
    
    face_attempts = 0
    face_detected = False

    while system_running:
        with frame_lock:
            if latest_frame is None:
                time.sleep(0.1)
                continue
            frame = latest_frame.copy()

        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        face_detected = False
        for encoding in face_encodings:
            if face_recognition.compare_faces([known_encoding], encoding)[0]:
                speak("Access granted.")
                cv2.destroyWindow("Face Verification")
                return True
            face_detected = True

        if face_detected:
            face_attempts += 1
            speak(f"Face not recognized. Attempt {face_attempts} of {MAX_FACE_ATTEMPTS}.")
            if face_attempts >= MAX_FACE_ATTEMPTS:
                cv2.destroyWindow("Face Verification")
                return voice_password_input()

        display_frame = cv2.resize(frame, (512, 384))
        cv2.imshow("Face Verification", display_frame)
        
        if cv2.waitKey(1) == ord('q'):
            system_running = False
            return False

# Voice Recognition with Rasa (chatbot)
def process_voice_command(text):
    global gesture_mode_active, camera_feed_open, system_running, audio_stream, keyboard_listener, threads
    text = text.lower()
    
    # Define keywords for robot commands
    move_words = ["come", "move", "go", "drive", "advance", "proceed", "continue"]
    turn_words = ["turn", "rotate", "spin"]
    stop_words = ["stop", "halt", "pause", "freeze", "brake", "wait", "rest"]
    shutdown_words = ["turn off", "switch off", "shut down", "power off"]
    diagonal_words = ["diagonal", "diagonally"]
    forward_words = ["forward", "front", "ahead", "straight"]
    backward_words = ["backward", "back", "reverse"]
    left_words = ["left", "leftward", "left side"]
    right_words = ["right", "rightward", "right side"]
    mode_change_words = ["change mode", "switch mode", "gesture control", "gesture mode", "voice control", "voice mode"]


    if any(word in text for word in shutdown_words):
        print("Shutting down via voice command...")
        speak("Shutting down")
        stop_motors()
        system_running = False
        if audio_stream:
            audio_stream.stop()
            audio_stream.close()
        if keyboard_listener:
            keyboard_listener.stop()
        time.sleep(0.1)
        current_thread = threading.current_thread()
        for thread in threads[:]:
            if thread != current_thread and thread.is_alive():
                thread.join(timeout=1)
        if camera_feed_open:
            cv2.destroyWindow("Gesture Mode")
        cv2.destroyAllWindows()
        GPIO.cleanup()
        clear_keyboard_buffer()
        sys.exit(0)


    if any(word in text for word in stop_words):
        speak("stopping motors")
        stop_motors()
        return

    if any(word in text for word in diagonal_words) and any(word in text for word in move_words):
        if any(lw in text for lw in left_words):
            if any(fw in text for fw in forward_words):
                speak("Diagonal left forward")
                move_diagonalleft_forward(50)
                return
            elif any(bw in text for bw in backward_words):
                speak("Diagonal left backward")
                move_diagonalleft_backward(50)
                return
            else:
                speak("Diagonal left forward (default)")
                move_diagonalleft_forward(50)
                return
        elif any(rw in text for rw in right_words):
            if any(fw in text for fw in forward_words):
                speak("Diagonal right forward")
                move_diagonalright_forward(50)
                return
            elif any(bw in text for bw in backward_words):
                speak("Diagonal right backward")
                move_diagonalright_backward(50)
                return
            else:
                speak("Diagonal right forward (default)")
                move_diagonalright_forward(50)
                return

    if any(word in text for word in turn_words):
        if any(word in text for word in left_words) and ("diagonally" not in text and " diagonal" not in text):
            speak("Turning left")
            turn_left(50)
            return
        elif any(word in text for word in right_words) and ("diagonally" not in text and " diagonal" not in text):
            speak("Turning right")
            turn_right(50)
            return

    if any(word in text for word in move_words):
        if any(word in text for word in forward_words) and ("diagonally" not in text and " diagonal" not in text) and not any(word in text for word in left_words) and not any(word in text for word in right_words):
            speak("Moving forward")
            move_forward(50)
            return
        elif any(word in text for word in backward_words) and ("diagonally" not in text and " diagonal" not in text) and not any(word in text for word in left_words) and not any(word in text for word in right_words):
            speak("Moving backward")
            move_backward(50)
            return
        elif any(word in text for word in left_words) and ("diagonally" not in text and " diagonal" not in text):
            speak("Moving left")
            move_left(50)
            return
        elif any(word in text for word in right_words) and ("diagonally" not in text and " diagonal" not in text):
            speak("Moving right")
            move_right(50)
            return


    if any(word in text for word in mode_change_words):
        if "gesture control" in text or "gesture mode" in text:
            if not gesture_mode_active:
                gesture_mode_active = True
                speak("Mode changed to gesture mode")
                print("Switched to Gesture Mode")
            else:
                speak("Gesture mode already active")
                print("Gesture mode already active")
            return
        elif "voice control" in text or "voice mode" in text:
            if gesture_mode_active:
                gesture_mode_active = False
                speak("Mode changed to voice mode")
                print("Switched to Voice Mode")
                if camera_feed_open:
                    cv2.destroyWindow("Gesture Mode")
                    camera_feed_open = False
            else:
                speak("Voice mode already active")
                print("Voice mode already active")
            return
        else:
            gesture_mode_active = not gesture_mode_active
            new_mode = "gesture" if gesture_mode_active else "voice"
            speak(f"Switching to {new_mode} mode")
            print(f"Switched to {new_mode} Mode")
            if not gesture_mode_active and camera_feed_open:
                cv2.destroyWindow("Gesture Mode")
                camera_feed_open = False
            return

    # Send to Rasa only if not a motor command
    print(f"Sending to Rasa: {text}")
    try:
        response = requests.post(RASA_URL, json={"sender": "user", "message": text})
        if response.status_code == 200:
            rasa_response = response.json()
            if rasa_response:
                for msg in rasa_response:
                    if "text" in msg:
                        speak(msg["text"])
        else:
            print(f"Failed to get response from Rasa: {response.status_code}")
    except Exception as e:
        print(f"Rasa request failed: {e}")
        
# voice Control
def voice_mode():
    global audio_stream, system_running, mic_muted
    model_path = "/home/venki/robot_project/vosk-model-small-en-us-0.15"
    model = Model(model_path)
    rec = KaldiRecognizer(model, 16000)
    q = sd_queue.Queue()

    def callback(indata, frames, time, status):
        if not mic_muted:
            q.put(bytes(indata))

    audio_stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                     channels=1, callback=callback)
    audio_stream.start()
        
    while not q.empty():
        try:
            q.get_nowait()
        except sd_queue.Empty:
            break

    speak("ROBOT activated")
    
    while not q.empty():
        try:
            q.get_nowait()
        except sd_queue.Empty:
            break

    try:
        while system_running:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                print("Heard:", text)
                process_voice_command(text)
            time.sleep(0.01)
    finally:
        if audio_stream:
            audio_stream.stop()
            audio_stream.close()
            
# Voice Thread Start
def start_voice():
    global threads
    thread = threading.Thread(target=voice_mode, daemon=True)
    thread.start()
    threads.append(thread)
    
# Camera Config
def camera_capture():
    global latest_frame, system_running
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        speak("Camera initialization failed. Shutting down.")
        system_running = False
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 512)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 384)
    while system_running:
        ret, frame = cap.read()
        if ret:
            with frame_lock:
                latest_frame = frame.copy()
        else:
            print("Camera read failed")
        time.sleep(0.01)
    cap.release()

def start_camera():
    global threads
    thread = threading.Thread(target=camera_capture, daemon=True)
    thread.start()
    threads.append(thread)
    
# Main Program
def main():
    global system_running, keyboard_listener, camera_feed_open
    setup_gpio()

    start_camera()
    time.sleep(1)
    
    speak("Robot Powered on, go through the face verification to proceed")

    if not face_verification():
        speak("Access denied")
        system_running = False
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout=1)
        cv2.destroyAllWindows()
        GPIO.cleanup()
        if audio_stream:
            audio_stream.stop()
            audio_stream.close()
        clear_keyboard_buffer()
        sys.exit(0)

    speak("Access granted.")
    
    start_gesture()
    start_voice()
    start_keyboard_listener()
    
    try:
        while system_running:
            if gesture_mode_active:
                with frame_lock:
                    if latest_frame is None:
                        time.sleep(0.1)
                        continue
                    frame = latest_frame.copy()
                display_frame = cv2.resize(frame, (512, 384))
                cv2.imshow("Gesture Mode", display_frame)
                camera_feed_open = True
            elif camera_feed_open:
                cv2.destroyWindow("Gesture Mode")
                camera_feed_open = False
                cv2.waitKey(1)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                system_running = False
                break
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        system_running = False
        if keyboard_listener:
            keyboard_listener.stop()
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout=1)
        if camera_feed_open:
            cv2.destroyWindow("Gesture Mode")
        cv2.destroyAllWindows()
        GPIO.cleanup()
        if audio_stream:
            audio_stream.stop()
            audio_stream.close()
        clear_keyboard_buffer()

if __name__ == "__main__":
    main()
