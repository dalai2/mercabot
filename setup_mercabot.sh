#!/bin/bash

# Define the path for the plist file
PLIST_FILE=~/Library/LaunchAgents/com.isaac.mercabot.plist

# Create the plist content
cat << EOF > $PLIST_FILE
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.isaac.mercabot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>source ~/Desktop/mercabot/venv/bin/activate && /usr/bin/python3 /Users/isaac/Desktop/mercabot/send_to_telegram_2.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

# Load the plist file into launchd
launchctl load $PLIST_FILE

echo "Plist file created and loaded successfully."
