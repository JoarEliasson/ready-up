import discord
import logging
from models import UserManager
from utils.helpers import handle_arrival
from discord.ext import commands
from config import RULES_MESSAGE
from tasks.check_intervals import check_intervals

class EventHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(RULES_MESSAGE)
        logging.info(f"Logged in as {self.bot.user} (ID: {self.bot.user.id})")
        self.bot.loop.create_task(check_intervals(self.bot))
        logging.info("Background task for scheduled notifications started.")

    @commands.Cog.listener()
    async def on_voice_state_update(bot, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        user_manager = UserManager()
        if before.channel is None and after.channel is not None:
            user_id = member.id
            user = user_manager.get_user(user_id)
            if user.eta and not user.arrived:
                user.arrived = True
                channel = bot.get_channel(user.channel_id)
                if channel:
                    await handle_arrival(user, user_id, channel)
