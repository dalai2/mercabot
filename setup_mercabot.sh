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
        <string>/Users/isaac/Desktop/mercabot/run_mercabot.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>11</integer>
        <key>Minute</key>
        <integer>0</integer>
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
