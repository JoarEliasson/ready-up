from discord.ext import commands
from config import RULES_MESSAGE

@commands.command(name="rules")
async def rules(ctx: commands.Context) -> None:
    """Display the bot rules. Usage: !rules"""
    await ctx.send(RULES_MESSAGE)