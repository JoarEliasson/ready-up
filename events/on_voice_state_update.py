import discord
from models import UserManager
from utils.helpers import handle_arrival

user_manager = UserManager()

async def on_voice_state_update(bot, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if before.channel is None and after.channel is not None:
        user_id = member.id
        user = user_manager.get_user(user_id)
        if user.eta and not user.arrived:
            user.arrived = True
            channel = bot.get_channel(user.channel_id)
            if channel:
                await handle_arrival(user, user_id, channel)