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

# Function to change the bot's status based on time
def update_status_based_on_time():
    global status
    current_time = datetime.now(ist)
    hour = current_time.hour
    
    # Change status based on time of the day
    if 10 <= hour < 13:  # 10 AM to 1 PM (Morning)
        status = "online"
        print(f"Changing status to 'Online' (Current Time: {current_time.strftime('%H:%M:%S')})")
    elif 13 <= hour < 14:  # 1 PM to 2 PM (Afternoon)
        status = "idle"
        print(f"Changing status to 'Idle' (Current Time: {current_time.strftime('%H:%M:%S')})")
    elif 15 <= hour < 20:  # 5 PM to 8 PM (Late Afternoon)
        status = "invisible"
        print(f"Changing status to 'Invisible' (Current Time: {current_time.strftime('%H:%M:%S')})")
    elif 20 <= hour < 23:  # 8 PM to 11 PM (Evening)
        status = "online"
        print(f"Changing status to 'Online' (Current Time: {current_time.strftime('%H:%M:%S')})")
    else:  # 11 PM to 10 AM (Late Night)
        status = "invisible"
        print(f"Changing status to 'Invisible' (Current Time: {current_time.strftime('%H:%M:%S')})")

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
