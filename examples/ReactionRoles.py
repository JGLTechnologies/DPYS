import disnake
from disnake.ext import commands

import dpys

TOKEN = "Your Token"
DATA_DIR = "Your dir goes here."

intents = disnake.Intents.default()
intents.guilds = True
intents.members = True

client = commands.AutoShardedBot(command_prefix="!", intents=intents)
_dpys_setup_complete = False


@client.event
async def on_ready():
    global _dpys_setup_complete
    if _dpys_setup_complete:
        return
    await dpys.setup(client, DATA_DIR)
    _dpys_setup_complete = True


@client.slash_command(name="rr")
@commands.has_permissions(administrator=True)
async def reaction_role_command(
    inter: disnake.ApplicationCommandInteraction,
    emoji: str = commands.Param(description="An emoji or list of emojis"),
    role: str = commands.Param(description="A role or list of roles."),
    title: str = commands.Param(description="The title for the embed"),
    description: str = commands.Param(description="The description for the embed"),
):
    await dpys.rr.command(inter, emoji, role, title, description)


@client.listen("on_raw_reaction_add")
async def role_add(payload: disnake.RawReactionActionEvent):
    await dpys.rr.add(payload, client)


@client.listen("on_raw_reaction_remove")
async def role_remove(payload: disnake.RawReactionActionEvent):
    await dpys.rr.remove(payload, client)


@client.slash_command(name="listrr")
@commands.has_role("Staff")
async def listrr(inter: disnake.ApplicationCommandInteraction):
    await dpys.rr.display(inter)


@client.slash_command(name="rrclear")
@commands.has_permissions(administrator=True)
async def rrclear(
    inter: disnake.ApplicationCommandInteraction,
    message_ids: str = commands.Param(
        description="Message id or a comma-separated list of ids, or 'all'."
    ),
):
    message_ids = message_ids.lower().strip()
    if message_ids == "all":
        await dpys.rr.clear_all(inter)
        return
    await dpys.rr.clear_one(inter, message_ids)


@client.listen("on_message_delete")
async def rr_clear_on_message_delete(message: disnake.Message):
    await dpys.rr.clear_on_message_delete(message)


@client.listen("on_channel_delete")
async def rr_clear_on_channel_delete(channel: disnake.abc.GuildChannel):
    if isinstance(channel, disnake.TextChannel):
        await dpys.rr.clear_on_channel_delete(channel)


@client.listen("on_thread_delete")
async def rr_clear_on_thread_delete(thread: disnake.Thread):
    await dpys.rr.clear_on_thread_delete(thread)


@client.listen("on_raw_bulk_message_delete")
async def rr_clear_on_raw_bulk_message_delete(
    payload: disnake.RawBulkMessageDeleteEvent,
):
    await dpys.rr.clear_on_bulk_message_delete(payload)


@client.listen("on_guild_remove")
async def clear_on_guild_remove(guild: disnake.Guild):
    await dpys.misc.clear_data_on_guild_remove(guild)


client.run(TOKEN)
