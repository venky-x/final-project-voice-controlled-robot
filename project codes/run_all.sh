
# Navigate to the robot_project directory
cd /home/venki/robot_project || exit 1

# Activate the virtual environment
source rasa_env/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }

# Start Rasa action server in the background
echo "Starting Rasa action server..."
cd rasa_bot
rasa run actions --port 5055 --debug > ../logs/rasa_actions.log 2>&1 & 
ACTIONS_PID=$!

# Start Rasa server in the background
echo "Starting Rasa server..."
rasa run --enable-api --cors "*" --debug --port 5005 > ../logs/rasa_server.log 2>&1 & 
RASA_PID=$!
cd ..

echo "Starting LCD animation..."
python3 lcd_animation.py > logs/lcd_animation.log 2>&1 &
ANIMATION_PID=$!

# Wait for Rasa server to load (3 minutes)
echo "Waiting for Rasa server to load (3 minutes)..."
sleep 130

# Start robot code in the foreground
echo "Starting robot code..."
python3 robot.py > logs/robot.log 2>&1

# Clean up background processes after robot.py exits
echo "Robot process ended. Shutting down Rasa processes..."
kill $ANIMATION_PID 2>/dev/null
kill $ACTIONS_PID $RASA_PID 2>/dev/null
wait $ACTIONS_PID $RASA_PID 2>/dev/null

# Exit immediately
echo "All processes stopped. Exiting."
exit 0
