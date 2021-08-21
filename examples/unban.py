import dpys
from discord.ext import commands

client = commands.AutoShardedBot(command_prefix="!")
TOKEN = "Your Token"

@client.command(name="unban")
async def unban(ctx, member):
    # This can take ID or name#discriminator
    # It will through an error you input something like nkjahsdklj
    # It's your job to make sure they input a member dpys can use
    await dpys.admin.unban(ctx, member)