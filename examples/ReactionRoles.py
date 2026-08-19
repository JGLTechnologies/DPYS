import asyncio
import os

import disnake
from disnake.ext import commands

import dpys

TOKEN = os.environ["DISCORD_TOKEN"]
DATA_DIR = os.environ.get("DPYS_DATA_DIR", "data")

intents = disnake.Intents.default()
intents.guilds = True

client = commands.AutoShardedBot(command_prefix="!", intents=intents)


@client.slash_command(name="rr")
@commands.guild_only()
@commands.has_permissions(manage_roles=True)
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
@commands.guild_only()
@commands.has_permissions(manage_roles=True)
async def listrr(inter: disnake.ApplicationCommandInteraction):
    await dpys.rr.display(inter)


@client.slash_command(name="rrclear")
@commands.guild_only()
@commands.has_permissions(manage_roles=True)
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


@client.listen("on_raw_message_delete")
async def rr_clear_on_raw_message_delete(payload: disnake.RawMessageDeleteEvent):
    await dpys.rr.clear_on_raw_message_delete(payload)


@client.listen("on_channel_delete")
async def rr_clear_on_channel_delete(channel: disnake.abc.GuildChannel):
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


async def main():
    await dpys.setup(client, DATA_DIR)
    try:
        await client.start(TOKEN)
    finally:
        await client.close()
        await dpys.close()


asyncio.run(main())
