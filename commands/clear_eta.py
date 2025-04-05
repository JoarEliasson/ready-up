from discord.ext import commands
from models import UserManager

user_manager = UserManager()

@commands.command(name="clear_eta")
async def clear_eta(ctx: commands.Context) -> None:
    """Clear your set ETA. Usage: !clear_eta"""
    user_id = ctx.author.id
    user = user_manager.get_user(user_id)
    if user.eta:
        user.eta = None
        user.arrived = False
        user.notifications_sent = set()
        await ctx.send(f"✅ <@{user_id}>, your ETA has been cleared.")
    else:
        await ctx.send("❌ You don't have an ETA set.")