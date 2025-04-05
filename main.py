import discord
from discord.ext import commands
import atexit
from commands import set_timezone
from config import DISCORD_TOKEN, USER_DATA_FILE
from models import UserManager
from commands.info import info
from commands.eta import set_eta
from commands.arrived import arrived
from commands.stats import stats
from commands.clear_eta import clear_eta
from commands.rules import rules
from events.on_ready import on_ready
from events.on_voice_state_update import on_voice_state_update

# Bot intents (permissions)
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Initialize the bot with the command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize UserManager
user_manager = UserManager()

# Load user data at startup
user_manager.load_from_file(USER_DATA_FILE)

# Save user data on exit
atexit.register(lambda: user_manager.save_to_file(USER_DATA_FILE))

# Add commands
bot.add_command(info)
bot.add_command(rules)
bot.add_command(set_eta)
bot.add_command(clear_eta)
bot.add_command(arrived)
bot.add_command(stats)
bot.add_command(set_timezone)

# Add events
bot.event(on_ready(bot))
bot.event(on_voice_state_update(bot))

# Start the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)