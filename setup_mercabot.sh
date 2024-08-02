# Define the path for the plist file
PLIST_FILE=~/Library/LaunchAgents/com.sandrajimenez.mercabot.plist

# Create the plist content
cat << EOF > $PLIST_FILE
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sandrajimenez.mercabot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>source ~/Desktop/mercabot/venv/bin/activate && /usr/bin/python3 /Users/isaac/Desktop/mercabot/send_to_telegram_2.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>10</integer>
        <key>Minute</key>
        <integer>50</integer>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/com.sandrajimenez.mercabot.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/com.sandrajimenez.mercabot.err</string>
</dict>
</plist>
EOF

# Load the plist file into launchd
launchctl unload $PLIST_FILE 2>/dev/null
launchctl load $PLIST_FILE

echo "Plist file created and loaded successfully."
