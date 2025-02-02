from keep_alive import keep_alive
import os
import sys
import json
import time
import requests
import websocket
import pytz
from datetime import datetime

# Set initial status (for now it will be "invisible")
status = "invisible"
custom_status= os.environ.get('custom_status')

usertoken = os.environ.get('token')
WEBHOOK_URL = "https://discord.com/api/webhooks/1335618527712903208/QsIKZXVZi481mO1eesAlBVCT1IiLKlNsHgcysbBqoGjHsAcOhzUH9Mbgi6pAOqr7yaqX"

if not usertoken:
    print("[ERROR] Please add a token inside Secrets.")
    sys.exit()

headers = {"Authorization": usertoken, "Content-Type": "application/json"}

validate = requests.get("https://canary.discordapp.com/api/v9/users/@me", headers=headers)
if validate.status_code != 200:
    print("[ERROR] Your token might be invalid. Please check it again.")
    sys.exit()

userinfo = requests.get("https://canary.discordapp.com/api/v9/users/@me", headers=headers).json()
username = userinfo["username"]
discriminator = userinfo["discriminator"]
userid = userinfo["id"]

# Set up IST timezone
tz= os.environ.get('timezone')
ist = pytz.timezone(tz)

# Function to calculate the next status update time in IST
def get_next_status_update_time_in_ist():
    current_time = datetime.now(ist)  # Current time in your original timezone (Dacca)
    hour = current_time.hour
    
    # Define time intervals for status changes
    if 10 <= hour < 13:  # 10 AM to 1 PM (Morning)
        next_time = current_time.replace(hour=13, minute=0, second=0, microsecond=0)
    elif 13 <= hour < 14:  # 1 PM to 2 PM (Afternoon)
        next_time = current_time.replace(hour=14, minute=0, second=0, microsecond=0)
    elif 15 <= hour < 20:  # 3 PM to 8 PM (Late Afternoon)
        next_time = current_time.replace(hour=20, minute=0, second=0, microsecond=0)
    elif 20 <= hour < 23:  # 8 PM to 11 PM (Evening)
        next_time = current_time.replace(hour=23, minute=0, second=0, microsecond=0)
    else:  # 11 PM to 10 AM (Late Night)
        next_time = current_time.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)  # Next morning 10 AM
    
    # Convert to IST for display in the embed
    next_time_ist = next_time.astimezone(pytz.timezone('Asia/Kolkata'))  # Convert to IST
    return next_time_ist

# Function to send an embedded message to Discord webhook
def send_status_embed(new_status):
    next_status_time_ist = get_next_status_update_time_in_ist()  # Get next update time in IST
    status_update= new_status.capitalize()
    embed = {
        "title": "Bot Status Update",
        "description": f"<@{userid}> Status Changed To **{status_update}** \n\n Next Status Update At `{next_status_time_ist.strftime('%B %d, %Y - %I:%M:%S %p')}`",  # Use IST time for next update
        "color": 0x00FF00 if new_status == "online" else 0xFFFF00 if new_status == "idle" else 0x808080,
        "footer": {
            "text": "Activity Simulator v2.1 | Developed by ZephyrDox"
        }
    }

    data = {
        "username": "Status Update",
        "embeds": [embed]
    }

    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code == 204:
        print(f"Embed sent successfully for status: {new_status}")
    else:
        print(f"Failed to send embed. Response: {response.status_code}, {response.text}")

# Function to change the bot's status based on time
def update_status_based_on_time():
    global status
    current_time = datetime.now(ist)
    hour = current_time.hour

    new_status = status  # Store the current status

    # Change status based on time of the day
    if 10 <= hour < 13:  # 10 AM to 1 PM (Morning)
        new_status = "online"
    elif 13 <= hour < 14:  # 1 PM to 2 PM (Afternoon)
        new_status = "idle"
    elif 15 <= hour < 20:  # 3 PM to 8 PM (Late Afternoon)
        new_status = "invisible"
    elif 20 <= hour < 23:  # 8 PM to 11 PM (Evening)
        new_status = "online"
    else:  # 11 PM to 10 AM (Late Night)
        new_status = "invisible"

    # If status has changed, update and send embed
    if new_status != status:
        status = new_status
        print(f"Changing status to '{status}' (Current Time: {current_time.strftime('%H:%M:%S')})")
        send_status_embed(status)

# Function to update the user's Discord presence status
def onliner(token, status):
    ws = websocket.WebSocket()
    ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
    start = json.loads(ws.recv())
    heartbeat = start["d"]["heartbeat_interval"]
    
    auth = {
        "op": 2,
        "d": {
            "token": token,
            "properties": {
                "$os": "Windows 10",
                "$browser": "Google Chrome",
                "$device": "Windows",
            },
            "presence": {"status": status, "afk": False},
        },
        "s": None,
        "t": None,
    }
    ws.send(json.dumps(auth))

    cstatus = {
        "op": 3,
        "d": {
            "since": 0,
            "activities": [
                {
                    "type": 4,
                    "state": custom_status,
                    "name": "Custom Status",
                    "id": "custom",
                }
            ],
            "status": status,
            "afk": False,
        },
    }
    ws.send(json.dumps(cstatus))

    online = {"op": 1, "d": "None"}
    time.sleep(heartbeat / 1000)
    ws.send(json.dumps(online))

def run_onliner():
    os.system("clear")
    print(f"Logged in as {username}#{discriminator} ({userid}).")
    while True:
        update_status_based_on_time()  # Check time and update status
        onliner(usertoken, status)  # Set the status on Discord
        time.sleep(60)  # Check and update every minute

keep_alive()
run_onliner()
