# DPYS

## The goal of DPYS is to make basic functionalities that every good bot needs easy to implement for beginners.

[DPYS](https://jgltechnologies.com/dpys) is a library that makes functionalites such as warnings, curse filter, reaction roles, anti mute evade, and many more easy to add to your bot.
<br>
All DPYS databases use the [aiosqlite library](https://aiosqlite.omnilib.dev/en/latest/).
<br>
Support for DPYS can be given [our Discord server](https://jgltechnologies.com/discord).
<br>
If you see any problems in the code or want to add a feature, create a pull request on [our Github](https://jgltechnologies.com/dpys/src).

<br>

install with pip
```
python -m pip install dpys
```

<br>

install with git
```
python -m pip install git+https://github.com/Nebulizer1213/dpys
```

<br>

Reaction Role Example

<br>

```python
import dpys
from discord.ext import commands

client = commands.AutoShardedBot(command_prefix="!")
TOKEN = "Your Token"

# Adds role on reaction.
@client.listen("on_raw_reaction_add")
async def role_add(payload):
    await dpys.rr.add(payload, "Your dir goes here.", client)


# Removes role when reaction is removed.
@client.listen("on_raw_reaction_remove")
async def role_remove(payload):
    await dpys.rr.remove(payload, "Your dir goes here.", client)


# Command to list all current reaction roles in the guild.
@client.command(name="listrr")
@commands.has_role("Staff")
async def listrr(ctx):
    await dpys.rr.display(ctx, "Your dir goes here.")


"""
Command to remove reaction role info from the database. Putting "all" as the id argument will wipe all reaction role data for the guild.
To remove specific ones put the message id as the id argument. You can put multiple just seperate by commas. Data is automatically wiped when the reaction role is deleted.
This will only need to be used if the reaction role was deleted with channel.purge.
The id can be found using the above command.
"""


@client.command(name="rrclear")
@commands.has_permissions(administrator=True)
async def rrclear(ctx, *, id):
    id = id.lower()
    if id == "all":
        await dpys.rr.clear_all(ctx, "Your dir goes here.")
        await ctx.message.delete()
    else:
        await dpys.rr.clear_one(ctx, "Your dir goes here.", id)
        await ctx.message.delete()


# Removes data for a reaction role when its message is deleted. Does not work with cahnnel.purge(). For that you need dpys.rr.clear_on_raw_bulk_message_delete().
@client.listen("on_message_delete")
async def rr_clear_on_message_delete(message):
    await dpys.rr.clear_on_message_delete(message, "Your dir goes here.")


# Removes data for a reaction role when its channel is deleted.
@client.listen("on_channel_delete")
async def rr_clear_on_channel_delete(channel):
    await dpys.rr.clear_on_message_delete(channel, "Your dir goes here.")


# Removes data for a reaction role when its message is deleted in channel.purge().
@client.listen("on_raw_bulk_message_delete")
async def rr_clear_on_raw_bulk_message_delete(payload):
    await dpys.rr.clear_on_raw_bulk_message_delete(payload, "Your dir goes here.")


# Clears all DPYS data for a guild when it is removed.
@client.listen("on_guild_remove")
async def rr_clear_on_guild_remove(guild):
    await dpys.misc.clear_data_on_guild_remove(guild, "Your dir goes here.")


"""
The command to create the reaction role.
It is used like this
!rr emoji @role <Embed Title> <Embed Description>
You can make one with multiple emojis and role.
!rr "emoji1, emoji2" "@role1, @role2" Title Description
If you don't understand where to use quotes and where not to think about it like this.
Whenever you add a space the bot thinks you are moving on to the next argument.
If you want an argument with spaces wrap it in quotes.
The only argument that does not need quotes if there are spaces is the description bescause it is the last argument.
"""

# Do not type hint discord.Role for the role argument
@client.command(name="rr", aliases=["reactionrole"])
@commands.has_permissions(administrator=True)
async def reaction_role_command(ctx, emoji, role, title, *, description):
    await ctx.message.delete()
    await dpys.rr.command(
        ctx, emoji, "Your dir goes here.", role, title=title, description=description
    )


client.run(TOKEN)
```

<br>
<br>

DPYS also has a utils extension that provides some useful features.

<br>

```python
from dpys import utils
import asyncio

async def foo():
    bar = "bar"
    result = await utils.var_can_be_type(bar, float)
    print(result)

asyncio.run(foo())

>>> False
```

