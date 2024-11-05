#!/bin/bash
# Run watchmedo to auto-restart the Python script on file changes
# Update the script to monitor changes in both the backend and frontend directories
watchmedo auto-restart --patterns="*.py" --recursive -- \
    python main.py
