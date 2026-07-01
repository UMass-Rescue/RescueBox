#!/usr/bin/env zsh
 
echo "Starting backend Server..."
# Run in background and pipe all output (errors and standard logs) to log
nohup poetry run python -m rb.api.main > backend.log 2>&1 &
echo "API Server running (PID: $!)"
sleep 30
echo "Starting frontend UI..."
nohup poetry run python frontend/main.py > frontend.log 2>&1 &
echo "Worker running (PID: $!)"

echo "-----------------------------------"
echo "Success! Both processes are running."
echo " open browser and enter http://localhost:8080 to use RescueBox"
echo "You can safely close this terminal window."