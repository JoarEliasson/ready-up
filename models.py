import json
from datetime import datetime, timedelta
import pytz
import os

BOT_TIMEZONE = pytz.timezone('Europe/Stockholm')

class User:
    def __init__(self):
        self.eta = None
        self.on_time_score = 0
        self.late_count = 0
        self.total_late_time = timedelta(0)
        self.arrived = False
        self.channel_id = 0
        self.notifications_sent = set()

    def to_dict(self):
        return {
            "eta": self.eta.isoformat() if self.eta else None,
            "on_time_score": self.on_time_score,
            "late_count": self.late_count,
            "total_late_time": self.total_late_time.total_seconds(),
            "arrived": self.arrived,
            "channel_id": self.channel_id,
            "notifications_sent": list(self.notifications_sent),
        }

    @classmethod
    def from_dict(cls, data):
        user = cls()
        user.eta = datetime.fromisoformat(data["eta"]).astimezone(BOT_TIMEZONE) if data.get("eta") else None
        user.on_time_score = data.get("on_time_score", 0)
        user.late_count = data.get("late_count", 0)
        user.total_late_time = timedelta(seconds=data.get("total_late_time", 0))
        user.arrived = data.get("arrived", False)
        user.channel_id = data.get("channel_id", 0)
        user.notifications_sent = set(data.get("notifications_sent", []))
        return user

class UserManager:
    def __init__(self):
        self.users = {}

    def load_from_file(self, filename):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                data = json.load(f)
            for user_id_str, user_data in data.items():
                user_id = int(user_id_str)
                self.users[user_id] = User.from_dict(user_data)

    def save_to_file(self, filename):
        data = {str(user_id): user.to_dict() for user_id, user in self.users.items()}
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    def get_user(self, user_id):
        if user_id not in self.users:
            self.users[user_id] = User()
        return self.users[user_id]