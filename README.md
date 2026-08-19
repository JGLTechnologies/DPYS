<a href="https://jgltechnologies.com/ddiscord">
<img src="https://discord.com/api/guilds/844418702430175272/embed.png">
</a>

# DPYS

## The goal of DPYS is to make common bot functionality easy to implement for beginners.

A big update was just released that added disnake support. If there are any bugs please report
them <a href="https://jgltechnologies.com/contact">here</a>.

[DPYS](https://jgltechnologies.com/dpys) is a library that makes functionality such as warnings, curse filtering,
reaction roles, anti mute evade, and many more easy to add to your bot. All DPYS databases use
the [aiosqlite library](https://aiosqlite.omnilib.dev/en/latest/). Support for DPYS can be given
in [our Discord server](https://jgltechnologies.com/disnake). If you see any problems in the code or want to add a
feature, create a pull request on [our Github repository](https://jgltechnologies.com/dpys/src).

<br>

Install from pypi

```
python -m pip install dpys
```

<br>

Install from github

```
python -m pip install git+https://github.com/JGLTechnologies/dpys
```

Setup

<br>

Set `DISCORD_TOKEN` in your environment before starting the bot (for example,
`$env:DISCORD_TOKEN = "your token"` in PowerShell). Never commit the token to the project.

```python
import asyncio
import os

import dpys
import disnake
from disnake.ext import commands

bot = commands.AutoShardedBot(command_prefix="!", intents=disnake.Intents.default())
TOKEN = os.environ["DISCORD_TOKEN"]


async def main():
    try:
        async with bot:
            await dpys.setup(bot, "database directory")
            await bot.start(TOKEN)
    finally:
        await dpys.close()


asyncio.run(main())
```

<br>

Reaction role example

<br>

```python
import asyncio
import os

import dpys
from disnake.ext import commands
import disnake

intents = disnake.Intents.default()
bot = commands.AutoShardedBot(command_prefix="!", intents=intents)
TOKEN = os.environ["DISCORD_TOKEN"]
DATA_DIR = os.environ.get("DPYS_DATA_DIR", "data")


# Do not type hint disnake.Role for the role argument
# Command to create the reaction role
@bot.slash_command(name="rr")
@commands.guild_only()
@commands.has_permissions(manage_roles=True)
async def reaction_role_command(inter: disnake.ApplicationCommandInteraction, emoji: str = commands.Param(
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
        inter, emoji, role, title, description
    )


# Adds role on reaction
@bot.listen("on_raw_reaction_add")
async def role_add(payload):
    await dpys.rr.add(payload, bot)


# Removes role when reaction is removed
@bot.listen("on_raw_reaction_remove")
async def role_remove(payload):
    await dpys.rr.remove(payload, bot)


# Command to list all current reaction roles in the guild
@bot.slash_command(name="listrr")
@commands.guild_only()
@commands.has_permissions(manage_roles=True)
async def listrr(inter: disnake.ApplicationCommandInteraction):
    await dpys.rr.display(inter)


# Command to remove reaction role info from the database
@bot.slash_command(name="rrclear")
@commands.guild_only()
@commands.has_permissions(manage_roles=True)
async def rrclear(inter: disnake.ApplicationCommandInteraction, message_ids: str = commands.Param(
    description="The id or list of ids of the reaction roles you want to remove")):
    """
    Putting "all" as the id argument will wipe all reaction role data for the guild.
    To remove specific ones put the message id as the id argument. You can put multiple just separate by commas.
    The id can be found using the above command.
    This command is still useful for cleaning up mappings whose roles were deleted.
    """
    message_ids = message_ids.lower()
    if message_ids == "all":
        await dpys.rr.clear_all(inter)
    else:
        await dpys.rr.clear_one(inter, message_ids)


# Removes data even when the deleted message was not cached.
@bot.listen("on_raw_message_delete")
async def rr_clear_on_raw_message_delete(payload):
    await dpys.rr.clear_on_raw_message_delete(payload)


# Removes data for a reaction role when its channel is deleted
@bot.listen("on_channel_delete")
async def rr_clear_on_channel_delete(channel):
    await dpys.rr.clear_on_channel_delete(channel)


# Removes data for a reaction role when its thread is deleted
@bot.listen("on_thread_delete")
async def rr_clear_on_thread_delete(thread):
    await dpys.rr.clear_on_thread_delete(thread)


# Removes data for a reaction role when its message is deleted in channel.purge()
@bot.listen("on_raw_bulk_message_delete")
async def rr_clear_on_raw_bulk_message_delete(payload):
    await dpys.rr.clear_on_bulk_message_delete(payload)


# Clears all DPYS data for a guild when it is removed
@bot.listen("on_guild_remove")
async def clear_on_guild_remove(guild):
    await dpys.misc.clear_data_on_guild_remove(guild)


async def main():
    try:
        async with bot:
            await dpys.setup(bot, DATA_DIR)
            await bot.start(TOKEN)
    finally:
        await dpys.close()


asyncio.run(main())
```

<br>
<br>

# Documentation

You will hear 'mute remove role' mentioned a lot. This is just an optional role that gets removed when a member is
muted, and added back when they are unmuted.

DPYS mutes are role-based. They do not disconnect a member who is already in a voice channel.

## Admin class

Kick:

```text
async def kick(inter: disnake.ApplicationCommandInteraction, member: disnake.Member,
               reason: typing.Optional[str] = None, msg: str = None) -> None
```

```python
import dpys


@bot.slash_command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(inter, member: disnake.Member = commands.Param(), reason: str = commands.Param(default=None)):
    await dpys.admin.kick(inter, member, reason)
```

<br>

Ban:

```text
async def ban(inter: disnake.ApplicationCommandInteraction, member: disnake.User,
              reason: typing.Optional[str] = None, msg: str = None) -> None
```

```python
@bot.slash_command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(inter, member: disnake.Member = commands.Param(), reason: str = commands.Param(default=None)):
    await dpys.admin.ban(inter, member, reason)
```

<br>

Softban:

```text
async def softban(inter: disnake.ApplicationCommandInteraction, member: disnake.Member,
                  reason: typing.Optional[str] = None, msg: str = None) -> None
```

```python
@bot.slash_command(name="softban")
@commands.has_permissions(ban_members=True)
async def softban(inter, member: disnake.Member = commands.Param(), reason: str = commands.Param(default=None)):
    await dpys.admin.softban(inter, member, reason)
```

<br>

Unban:

```text
async def unban(inter: ApplicationCommandInteraction, member: disnake.User, msg: str = None) -> bool:
```

```python
@bot.slash_command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(inter, member: disnake.User = commands.Param()):
    await dpys.admin.unban(inter, member)
```

<br>

Mute:

```text
async def mute(inter: disnake.ApplicationCommandInteraction, member: disnake.Member, role_add: int,
               role_remove: typing.Optional[int] = None, reason: str = None, msg: str = None) -> bool
```

```python
@bot.slash_command(name="mute")
@commands.has_permissions(manage_roles=True)
async def mute(inter, member: disnake.Member = commands.Param(), reason: str = commands.Param(default=None)):
    await dpys.admin.mute(inter, member, MUTE_ROLE_ID, MUTE_REMOVE_ROLE_ID, reason=reason)
```

<br>

Unmute:

```text
async def unmute(inter: disnake.ApplicationCommandInteraction, member: disnake.Member, role_remove: int,
                 role_add: typing.Optional[int] = None, msg: str = None) -> bool
```

```python
@bot.slash_command(name="unmute")
@commands.has_permissions(manage_roles=True)
async def unmute(inter, member: disnake.Member = commands.Param()):
    await dpys.admin.unmute(inter, member, MUTE_ROLE_ID, MUTE_REMOVE_ROLE_ID)
```

<br>

Clear:

```text
async def clear(inter: disnake.ApplicationCommandInteraction, amount: typing.Optional[int] = 100,
                 msg: str = None) -> int
```

```python
@bot.slash_command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(inter, amount: int = commands.Param(default=100)):
    await dpys.admin.clear(inter, amount)
```

<br>

Timeout:

```text
async def timeout(inter: ApplicationCommandInteraction, member: discord.Member,
                  duration: Union[float, datetime.timedelta] = None, until: datetime.datetime = None,
                  reason: typing.Optional[str] = None, msg: str = None) -> None:
```

```python
@bot.slash_command(name="timeout")
@commands.has_permissions(moderate_members=True)
async def timeout(inter, member: disnake.Member = commands.Param(),
                  seconds: int = commands.Param(), reason: str = commands.Param(None)):
    await dpys.admin.timeout(inter, member, duration=seconds, reason=reason)
```

<br>

## mute_on_join Class

Add Member:

```text
async def mute_add(guild: disnake.Guild, member: disnake.Member) -> None
```

```python
@bot.slash_command(name="mute")
@commands.has_permissions(manage_roles=True)
async def mute(inter, member: disnake.Member = commands.Param(), reason: str = commands.Param(default=None)):
    if await dpys.admin.mute(inter, member, MUTE_ROLE_ID, MUTE_REMOVE_ROLE_ID, reason):
        await dpys.mute_on_join.mute_add(inter.guild, member)
```

<br>

Remove Member:

```text
async def mute_remove(guild: disnake.Guild, member: disnake.Member) -> None
```

```python
@bot.slash_command(name="unmute")
@commands.has_permissions(manage_roles=True)
async def unmute(inter, member: disnake.Member = commands.Param()):
    if await dpys.admin.unmute(inter, member, MUTE_ROLE_ID, MUTE_REMOVE_ROLE_ID):
        await dpys.mute_on_join.mute_remove(inter.guild, member)
```

<br>

Mute On Join Event Listener:

This listener requires the **Server Members Intent** in the Discord Developer Portal and `intents.members = True` in
your bot.

```text
async def mute_on_join(member: disnake.Member, role_add: int, role_remove: Optional[int] = None) -> None
```

```python
@bot.listen("on_member_join")
async def mute_on_join(member: disnake.Member):
    await dpys.mute_on_join.mute_on_join(member, MUTE_ROLE_ID, MUTE_REMOVE_ROLE_ID)
```

<br>

Manual Unmute Check:

```text
async def manual_unmute_check(before: disnake.Member, after: disnake.Member, roleid: int) -> None
```

```python
import dpys


@bot.listen("on_member_update")
async def manual_unmute_check(before: disnake.Member, after: disnake.Member):
    await dpys.mute_on_join.manual_unmute_check(before, after, MUTE_ROLE_ID)
```

<br>

## rr Class

Command:

```text
async def command(inter: disnake.ApplicationCommandInteraction, emoji: str, role: str, title: str,
                  description: str) -> None
```

```python
# Don't type hint disnake.Role for the role parameter
@bot.slash_command(name="rr")
@commands.guild_only()
@commands.has_permissions(manage_roles=True)
async def reactionrole(inter, emoji: str = commands.Param(), role: str = commands.Param(),
                       title: str = commands.Param(), description: str = commands.Param()):
    await dpys.rr.command(inter, emoji, role, title, description)
```

<br>

Command To List Reaction Roles:

```text
async def display(inter: ApplicationCommandInteraction) -> None
```

```python
@bot.slash_command(name="listrr")
@commands.guild_only()
@commands.has_permissions(manage_roles=True)
async def listrr(inter: disnake.ApplicationCommandInteraction):
    await dpys.rr.display(inter)
```

<br>

On Raw Reaction Add Event Listener:

```text
async def add(payload: disnake.RawReactionActionEvent, bot: commands.Bot) -> None
```

```python
@bot.listen('on_raw_reaction_add')
async def rr_add(payload: disnake.RawReactionActionEvent):
    await dpys.rr.add(payload, bot)
```

<br>

On Raw Reaction Remove Event Listener:

```text
async def remove(payload: disnake.RawReactionActionEvent, bot: commands.Bot) -> None
```

```python
@bot.listen('on_raw_reaction_remove')
async def rr_remove(payload: disnake.RawReactionActionEvent):
    await dpys.rr.remove(payload, bot)
```

<br>

Clear Reaction Role command:

```text
async def clear_all(inter: disnake.ApplicationCommandInteraction) -> None


async def clear_one(inter: disnake.ApplicationCommandInteraction, message_id: int | str) -> None
```

```python
@bot.slash_command(name="rrclear")
@commands.guild_only()
@commands.has_permissions(manage_roles=True)
async def rrclear(inter, message_ids: str = commands.Param()):
    if message_ids.lower() == "all":
        await dpys.rr.clear_all(inter)
    else:
        await dpys.rr.clear_one(inter, message_ids)
```

<br>

Event Listeners To Clear Reaction Role Data:

```python
@bot.listen("on_raw_message_delete")
async def rr_clear_on_raw_message_delete(payload: disnake.RawMessageDeleteEvent):
    await dpys.rr.clear_on_raw_message_delete(payload)


@bot.listen("on_raw_bulk_message_delete")
async def rr_clear_on_raw_bulk_message_delete(payload: disnake.RawBulkMessageDeleteEvent):
    await dpys.rr.clear_on_bulk_message_delete(payload)


@bot.listen("on_channel_delete")
async def rr_clear_on_channel_delete(channel: disnake.abc.GuildChannel):
    await dpys.rr.clear_on_channel_delete(channel)


@bot.listen("on_thread_delete")
async def rr_clear_on_thread_delete(thread: disnake.Thread):
    await dpys.rr.clear_on_thread_delete(thread)
```

<br>

## warnings Class

Warn:

```text
async def warn(inter: ApplicationCommandInteraction, member: disnake.Member,
               reason: str | None = None, expires: float | int | None = -1) -> None
```

```python
import time


@bot.slash_command(name="warn")
@commands.guild_only()
@commands.has_permissions(moderate_members=True)
async def warn(inter: disnake.ApplicationCommandInteraction, member: disnake.Member = commands.Param(),
               reason: str = commands.Param(default=None)):
    # Warning will expire in 1 day
    await dpys.warnings.warn(inter, member, reason, time.time() + 86400)
```

<br>

Unwarn:

```text
async def unwarn(inter: disnake.ApplicationCommandInteraction, member, number: typing.Union[int, str]) -> bool
```

```python
# Pass in "all" as the number parameter to clear all warnings from a member
@bot.slash_command(name="unwarn")
@commands.guild_only()
@commands.has_permissions(moderate_members=True)
async def unwarn(inter: disnake.ApplicationCommandInteraction, member: disnake.Member = commands.Param(),
                 number: str = commands.Param(default="all")):
    await dpys.warnings.unwarn(inter, member, number)
```

<br>

Punish:

```text
async def punish(inter: ApplicationCommandInteraction, member: discord.Member,
                 punishments: typing.Mapping[int, Punishment],
                 add_role: typing.Optional[int] = None, remove_role: typing.Optional[int] = None,
                 before: Optional[
                     Callable[[int, Punishment, disnake.Member], Awaitable[Optional[disnake.Message]]]] = None) -> None:
```

```python
@bot.slash_command(name="warn")
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def warn(inter: disnake.ApplicationCommandInteraction, member: disnake.Member = commands.Param(),
               reason: str = commands.Param(default=None)):
    await dpys.warnings.warn(inter, member, reason)
    # This will do nothing for the first 2 warnings, but on the third warning it will kick the member.
    # Valid punishments for dpys.warnings.Punishment are kick, ban, mute, temp_ban, temp_mute, timeout
    # If you want to mute you have to pass in you mute role id and an optional mute remove role id.
    # Temporary punishments require a positive duration (in seconds) in the Punishment constructor.
    await dpys.warnings.punish(inter, member,
                               {3: dpys.warnings.Punishment("kick")})
```

<br>

If you use expiring warnings, temp bans, or temp mutes, include this cog in your bot. New temp-mute rows store the exact
role changes; the role callbacks also keep older database rows compatible during upgrades.

```python
from disnake.ext import commands, tasks
import dpys

MUTE_ROLE_ID = 123456789012345678
MUTE_REMOVE_ROLE_ID = None


async def get_mute_role_id(guild_id: int) -> int:
    return MUTE_ROLE_ID


async def get_mute_remove_role_id(guild_id: int) -> int | None:
    return MUTE_REMOVE_ROLE_ID


class DpysLoops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dpys_tempmute_loop.start()
        self.dpys_tempban_loop.start()
        self.dpys_expire.start()

    def cog_unload(self):
        self.dpys_tempmute_loop.cancel()
        self.dpys_tempban_loop.cancel()
        self.dpys_expire.cancel()

    @tasks.loop(seconds=1)
    async def dpys_tempmute_loop(self):
        await dpys.warnings.temp_mute_loop(
            self.bot, get_mute_role_id, get_mute_remove_role_id
        )

    @dpys_tempmute_loop.before_loop
    async def before_dpys_tempmute_loop(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=30)
    async def dpys_expire(self):
        await dpys.warnings.expire_loop()

    @dpys_expire.before_loop
    async def before_dpys_expire(self):
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=1)
    async def dpys_tempban_loop(self):
        await dpys.warnings.temp_ban_loop(self.bot)

    @dpys_tempban_loop.before_loop
    async def before_dpys_tempban_loop(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(DpysLoops(bot))
```

<br>

Warnings:

```text
async def warnings(inter: disnake.ApplicationCommandInteraction, member: disnake.Member, warn_num: int = 0) -> None
```

`warn_num` is the warning you want to see. Set it to 0 to see all active warnings paginated five per page.

```python
@bot.slash_command(name="warnings")
@commands.guild_only()
@commands.has_permissions(moderate_members=True)
async def warnings(inter: disnake.ApplicationCommandInteraction, member: disnake.Member = commands.Param()):
    await dpys.warnings.warnings(inter, member)
```

<br>

```text
async def warnings_list(guild: int, member_id: int) -> list[str]
```

Returns the active warnings for a member.

<br>

## curse Class

Add Word:

```text
async def add_banned_word(inter: disnake.ApplicationCommandInteraction, word: str) -> None
```

```python
@bot.slash_command(name="addword")
@commands.has_permissions(manage_messages=True)
async def add_word(inter: disnake.ApplicationCommandInteraction, curses: str = commands.Param()):
    await dpys.curse.add_banned_word(inter, curses)
```

<br>

Remove Word:

```text
async def remove_banned_word(inter: disnake.ApplicationCommandInteraction, word: str) -> None
```

```python
@bot.slash_command(name="removeword")
@commands.has_permissions(manage_messages=True)
async def remove_word(inter: disnake.ApplicationCommandInteraction, curses: str = commands.Param()):
    await dpys.curse.remove_banned_word(inter, curses)
```

<br>

Clear Words:

```text
async def clear_words(inter: disnake.ApplicationCommandInteraction) -> None
```

```python
@bot.slash_command(name="clearwords")
@commands.has_permissions(manage_messages=True)
async def clear_words(inter: disnake.ApplicationCommandInteraction):
    await dpys.curse.clear_words(inter)
```

<br>

Message Filter Listeners:

Enable `intents.message_content = True` when constructing the bot, then register both listeners:

```python
@bot.listen("on_message")
async def filter_message(message: disnake.Message):
    await dpys.curse.message_filter(message)


@bot.listen("on_message_edit")
async def filter_edited_message(before: disnake.Message, after: disnake.Message):
    await dpys.curse.message_edit_filter(after)
```

<br>

## misc Class

Reload:

```text
async def reload(inter: disnake.ApplicationCommandInteraction, bot: commands.BotBase, cogs: list[str]) -> None
```

```python
@bot.slash_command(name="reload")
@commands.is_owner()
async def reload(inter: disnake.ApplicationCommandInteraction):
    cogs = ["cogs.admin", "cogs.fun", "cogs.misc"]
    await dpys.misc.reload(inter, bot, cogs)
```

<br>

Clear DPYS Data On Guild Remove:

```python
@bot.listen("on_guild_remove")
async def clear_dpys_data(guild: disnake.Guild):
    await dpys.misc.clear_data_on_guild_remove(guild)
```


