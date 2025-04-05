import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
USER_DATA_FILE = "user_data.json"

RULES_MESSAGE = """
**================== ReadyUp Bot Rules ==================**

**1. Set Your Expected Arrival Time (ETA):**
   - Use `!eta HH:MM` to set your ETA in 24-hour format (e.g., `!eta 19:00`).

**2. Mark Your Arrival:**
   - Automatically: Join any voice channel.
   - Manually: Use `!arrived` in chat.

**3. Notifications:**
   - You will receive reminders if you are late:
     - 1 minute before your ETA
     - 15, 30, and 60 minutes after your ETA
     - A final no-show alert 24 hours after your ETA if you haven't arrived.

**4. Check Statistics:**
   - Use `!stats` to view your own stats.
   - Use `!stats @User` to view another user's stats.
   - Stats include on-time arrivals, late arrivals, and total late time.

**5. Clear Your ETA:**
   - Use `!clear_eta` to remove your set ETA.

**6. View These Rules:**
   - Use `!rules` to display this message again.

**======================================================**
"""

INFO_MESSAGE = """
all the bot commands
**================== ReadyUp Bot Info ==================**
**Set Your Expected Arrival Time (ETA):**
   - Use `!eta HH:MM` to set your ETA in 24-hour format (e.g., `!eta 19:00`).
**Mark Your Arrival:**
    - Automatically: Join any voice channel.
    - Manually: Use `!arrived` in chat.
**Commands**
    - All commands start with `!`
    - `!eta HH:MM`: Set your ETA.
    - `!arrived`: Mark yourself as arrived.
    - `!clear_eta`: Clear your ETA.
    - `!stats`: View your stats.
    - `!stats @User`: View another user's stats.
    - `!set_timezone`: Set your timezone.
    - `!rules`: View the rules.
    - `!info`: View this info message.
**======================================================**
"""