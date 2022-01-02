import dpys
from disnake.ext import commands
import disnake

client = commands.AutoShardedBot(command_prefix="!")
TOKEN = "Your Token"


# Do not type hint disnake.Role for the role argument
# Command to create the reaction role
@commands.slash_command(name="rr")
@commands.has_permissions(administrator=True)
async def reaction_role_command(inter: disnake.MessageCommandInteraction, emoji: str = commands.Param(
    description="An emoji or list of emojis"),
                                role: str = commands.Param(
                                    description="a Role or list of roles."),
                                title: str = commands.Param(description="The title for the embed"),
                                description: str = commands.Param(description="The description for the embed")):
    """
    It is used like this
    /rr emoji @role <Embed Title> <Embed Description>
    You can make one with multiple emojis and role.
    /rr emojis: emoji1, emoji2 roles: @role1, @role2 title Description
    Just make sure to separate the emojis and roles with commas and match the position of the roles and emojis.
    """
    await dpys.rr.command(
        inter, emoji, "Your dir goes here.", role, title, description
    )


# Adds role on reaction
@client.listen("on_raw_reaction_add")
async def role_add(payload):
    await dpys.rr.add(payload, "Your dir goes here.", client)


# Removes role when reaction is removed
@client.listen("on_raw_reaction_remove")
async def role_remove(payload):
    await dpys.rr.remove(payload, "Your dir goes here.", client)


# Command to list all current reaction roles in the guild
@commands.slash_command(name="listrr")
@commands.has_role("Staff")
async def listrr(inter: disnake.MessageCommandInteraction):
    await dpys.rr.display(inter, "Your dir goes here.")


# Command to remove reaction role info from the database
@commands.slash_command(name="rrclear")
@commands.has_permissions(administrator=True)
async def rrclear(inter: disnake.MessageCommandInteraction, id: str = commands.Param(
    description="The id or list of ids of the reaction roles you want to remove")):
    """
    Putting "all" as the id argument will wipe all reaction role data for the guild.
    To remove specific ones put the message id as the id argument. You can put multiple just separate by commas.
    The id can be found using the above command.
    This command does not need to be added if you use the event listeners bellow.
    """
    id = id.lower()
    if id == "all":
        await dpys.rr.clear_all(inter, "Your dir goes here.")
    else:
        await dpys.rr.clear_one(inter, "Your dir goes here.", int(id))


# Removes data for a reaction role when its message is deleted. Does not work with channel.purge(). For that you need dpys.rr.clear_on_raw_bulk_message_delete()
@client.listen("on_message_delete")
async def rr_clear_on_message_delete(message):
    await dpys.rr.clear_on_message_delete(message, "Your dir goes here.")


# Removes data for a reaction role when its channel is deleted
@client.listen("on_channel_delete")
async def rr_clear_on_channel_delete(channel):
    await dpys.rr.clear_on_channel_delete(channel, "Your dir goes here.")


# Removes data for a reaction role when its channel is deleted
@client.listen("on_thread_delete")
async def rr_clear_on_thread_delete(thread):
    await dpys.rr.clear_on_thread_delete(thread, "Your dir goes here.")


# Removes data for a reaction role when its message is deleted in channel.purge()
@client.listen("on_raw_bulk_message_delete")
async def rr_clear_on_raw_bulk_message_delete(payload):
    await dpys.rr.clear_on_raw_bulk_message_delete(payload, "Your dir goes here.")


# Clears all DPYS data for a guild when it is removed
@client.listen("on_guild_remove")
async def clear_on_guild_remove(guild):
    await dpys.misc.clear_data_on_guild_remove(guild, "Your dir goes here.")


client.run(TOKEN)
