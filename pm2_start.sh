#!/bin/bash

# Path to the PM2 configuration file
CONFIG_FILE="/root/dev/Workload_ChatGPT/pm2_ecosystem.config.js"

# Change to the application directory
cd /root/dev/Workload_ChatGPT

# Parse arguments
if [ "$1" == "start" ]; then
    echo "Starting Workload_ChatGPT with PM2..."
    pm2 start $CONFIG_FILE --name "Workload_Main"
elif [ "$1" == "stop" ]; then
    echo "Stopping Workload_ChatGPT..."
    pm2 stop Workload_ChatGPT
elif [ "$1" == "restart" ]; then
    echo "Restarting Workload_ChatGPT..."
    pm2 restart Workload_ChatGPT
elif [ "$1" == "status" ]; then
    echo "Workload_ChatGPT status:"
    pm2 status Workload_ChatGPT
elif [ "$1" == "run" ]; then
    # Option to run directly without PM2 (for testing)
    echo "Running Workload_ChatGPT without PM2 (test mode)..."
    python3 workload_main.py
else
    echo "Usage: $0 {start|stop|restart|status|run}"
    exit 1
fi

