from discord.ext import commands
from config import INFO_MESSAGE

@commands.command(name="info")
async def info(ctx: commands.Context) -> None:
    """Display the commands. Usage: !info"""
    await ctx.send(INFO_MESSAGE)