import discord
from discord.ext import commands
import atexit
from config import DISCORD_TOKEN, USER_DATA_FILE
from models import UserManager
from commands.info import info
from commands.eta import set_eta
from commands.arrived import arrived
from commands.stats import stats
from commands.clear_eta import clear_eta
from commands.rules import rules
from events.ready_and_voice import EventHandler
# Not yet implemented
#from commands.set_timezone import set_timezone

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
# Not yet implemented
#bot.add_command(set_timezone)

# Setup hook for events
async def setup_hook():
    await bot.add_cog(EventHandler(bot))

# Register the setup hook
bot.setup_hook = setup_hook

# Start the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)