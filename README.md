# final-project-voice-controlled-robot

This repository contains the code for a multi-modal control robot designed to assist the elderly. The robot features face and voice recognition, gesture and keyboard control, and a Rasa-based NLU system for interaction, with emotional feedback via an LCD screen. It uses a Raspberry Pi 4B with Mecanum wheels for omnidirectional movement.

Prerequisites


Hardware:

1.Raspberry Pi 4B (4GB RAM)

2.Mecanum wheels with DC motors

3.TB6612FNG motor driver

4.720p USB camera

5.USB microphone and speaker

6.3.5-inch LCD screen

7.5V/3A USB-C power supply



Software:

1.Raspberry Pi OS (32-bit) - Debian Bullseye 11 - Python 3.9.2

2.Required libraries: opencv-python, mediapipe, face_recognition, vosk, rasa, RPi.GPIO, requests, pygame, sounddevice, pynput, espeak-ng

3.Rasa framework (To be installed and configured)

4.vosk-model-small-en-us-0.15 (To be installed)


Installation:

1.download the project codes file

2.Install dependencies using pip install -r requirements.txt

Set up the Rasa environment:

   1. Navigate to the rasa_bot directory.

   2. Run rasa train to train the NLU model.


Configure hardware:

Connect the Mecanum wheels, motor driver, camera, microphone, speaker, and LCD to the Raspberry Pi as per the hardware block diagram.

Ensure GPIO pins are correctly mapped in robot.py.


Usage:

Start the system by running the initialization script:

./run_all.sh

This script launches the robot program, Rasa server, and LCD animation concurrently.



Interact with the robot:

1.Face Verification: Use the camera for initial authentication (voice password fallback with "robot").

2.Voice Commands: Speak commands like "move forward" or ask for date/time/jokes via the microphone.

3.Gesture Control: Move your hand in front of the camera (e.g., left/right for navigation).

4.Keyboard Control: Press 'q' (forward), 'w' (backward), 'e' (left), 'r' (right), 'a' (stop), 'c' (shutdown).

5.Monitor emotional feedback on the LCD screen during operation.


Files

1.rasa_bot/: Contains Rasa configuration files (e.g., domain.yml, config.yml, rules.yml, actions.py) for NLU and chatbot functionality.

2.lcd_animation.py: Handles LCD screen animations using Pygame for emotional feedback.

3.robot.py: Main script integrating face verification, voice/gesture/keyboard control, and motor operations.

4.run_all.sh: Bash script to automate system startup.

Contributing

Feel free to fork this repository, submit issues, or create pull requests for enhancements (e.g., noise cancellation, stereo vision integration).

## License

This project is licensed under the [MIT License](LICENSE).
