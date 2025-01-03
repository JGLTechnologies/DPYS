<a href="https://jgltechnologies.com/ddiscord">
<img src="https://discord.com/api/guilds/844418702430175272/embed.png">
</a>

# DPYS

## The goal of DPYS is to make basic functionalities that every good bot needs easy to implement for beginners.

A big update was just released that added disnake support. If there are any bugs please report
them <a href="https://jgltechnologies.com/contact">here</a>.

[DPYS](https://jgltechnologies.com/dpys) is a library that makes functionalites such as warnings, curse filter, reaction
roles, anti mute evade, and many more easy to add to your bot. All DPYS databases use
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

```python
import dpys
from disnake.ext import commands

bot = commands.AutoShardedBot(command_prefix="!")
TOKEN = "Your Token"

bot.loop.create_task(dpys.setup(bot, "database directory"))
bot.run()
```

<br>

Reaction role example

<br>

```python
import dpys
from disnake.ext import commands
import disnake

bot = commands.AutoShardedBot(command_prefix="!")
TOKEN = "Your Token"


# Do not type hint disnake.Role for the role argument
# Command to create the reaction role
@bot.slash_command(name="rr")
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
async def listrr(inter: disnake.ApplicationCommandInteraction):
    await dpys.rr.display(inter)


# Command to remove reaction role info from the database
@bot.slash_command(name="rrclear")
async def rrclear(inter: disnake.ApplicationCommandInteraction, id: str = commands.Param(
    description="The id or list of ids of the reaction roles you want to remove")):
    """
    Putting "all" as the id argument will wipe all reaction role data for the guild.
    To remove specific ones put the message id as the id argument. You can put multiple just separate by commas.
    The id can be found using the above command.
    This command does not need to be added if you use the event listeners bellow.
    """
    id = id.lower()
    if id == "all":
        await dpys.rr.clear_all(inter)
    else:
        await dpys.rr.clear_one(inter, int(id))


# Removes data for a reaction role when its message is deleted. Does not work with channel.purge(). For that you need dpys.rr.clear_on_raw_bulk_message_delete()
@bot.listen("on_message_delete")
async def rr_clear_on_message_delete(message):
    await dpys.rr.clear_on_message_delete(message)


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
    await dpys.rr.clear_on_raw_bulk_message_delete(payload)


# Clears all DPYS data for a guild when it is removed
@bot.listen("on_guild_remove")
async def clear_on_guild_remove(guild):
    await dpys.misc.clear_data_on_guild_remove(guild)


bot.loop.create_task(dpys.setup(bot, DIR))
bot.run(TOKEN)
```

<br>
<br>

# Documentation

You will hear 'mute remove role' mentioned a lot. This is just an optional role that gets removed when a member is
muted, and added back when they are unmuted.

## Admin class

Kick:

```python
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

```python
async def ban(inter: disnake.ApplicationCommandInteraction, member: disnake.Member,
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

```python
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

```python
async def unban(inter: ApplicationCommandInteraction, member: typing.Union[str, int], msg: str = None) -> bool:
```

```python
@bot.slash_command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(inter, member: string = commands.Param()):
    await dpys.admin.unban(inter, member)
```

<br>

Mute:

```python
async def mute(inter: disnake.ApplicationCommandInteraction, member: disnake.Member, role_add: int,
               role_remove: typing.Optional[int] = None, reason: str = None, msg: str = None) -> None
```

```python
@bot.slash_command(name="mute")
async def mute(inter, member: disnake.Member = commands.Param(), reason: str = commands.Param(default=None)):
    await dpys.admin.mute(inter, member, MUTE_ROLE_ID, MUTE_REMOVE_ROLE_ID, reason=reason)
```

<br>

Unmute:

```python
async def unmute(inter: disnake.ApplicationCommandInteraction, member: disnake.Member, role_remove: int,
                 role_add: typing.Optional[int] = None, msg: str = None) -> bool
```

```python
@bot.slash_command(name="unmute")
async def unmute(inter, member: disnake.Member = commands.Param()):
    await dpys.admin.unmute(inter, member, MUTE_REMOVE_ROLE_ID, MUTE_ROLE_ID)
```

<br>

Clear:

```python
async def clear(inter: disnake.ApplicationCommandInteraction, amount: typing.Optional[int] = 99999999999999999,
                msg: str = None) -> int
```

```python
@bot.slash_command(name="clear")
async def clear(inter, amount: int = commands.Param(default=99999999999999999)):
    await dpys.admin.clear(inter, amount)
```

<br>

Timeout:

```python
async def timeout(inter: ApplicationCommandInteraction, member: discord.Member,
                  duration: Union[float, datetime.timedelta] = None, until: datetime.datetime = None,
                  reason: typing.Optional[str] = None, msg: str = None) -> None:
```

```python
@bot.slash_command(name="timeout")
async def timeout(inter, seconds: int = commands.Param(), reason: str = commands.Param(None)):
    await dpys.admin.timeout(inter, duration=seconds, reason=reason)
```

<br>

## mute_on_join Class

Add Member:

```python
async def mute_add(guild: disnake.Guild, member: disnake.Member) -> None
```

```python
@bot.slash_command(name="mute")
async def mute(inter, member: dicord.Member = commands.Param(), reason: str = commands.Param(default=None)):
    await dpys.admin.mute(inter, member, MUTE_ROLE_ID, MUTE_REMOVE_ROLE_ID, reason)
    await dpys.mute_on_join.mute_add(inter.guild, member)
```

<br>

Remove Member:

```python
async def mute_remove(guild: disnake.Guild, member: disnake.Member) -> None
```

```python
@bot.slash_command(name="unmute")
async def unmute(inter, member: dicord.Member = commands.Param()):
    await dpys.admin.unmute(inter, member, MUTE_ROLE_ID, MUTE_REMOVE_ROLE_ID)
    await dpys.mute_on_join.mute_remove(inter.guild, member)
```

<br>

Mute On Join Event Listener:

```python
async def mute_on_join(member: disnake.Member, role_add: int, role_remove: Optional[int] = None) -> None
```

```python
@bot.listen("on_member_join")
async def mute_on_join(member: disnake.Member):
    await dpys.mute_on_join.mute_on_join(member, MUTE_ROLE_ID, MUTE_REMOVE_ROLE)
```

<br>

Manual Unmute Check:

```python
async def manual_unmute_check(after: disnake.Member, roleid: int) -> None
```

```python
import dpys


@bot.listen("on_member_update")
async def manual_unmute_check(before: disnake.Member, after: disnake.Member):
    await dpys.mute_on_join.manual_unmute_check(after, MUTE_ROLE_ID)
```

<br>

## rr Class

Command:

```python
async def command(inter: disnake.ApplicationCommandInteraction, emoji: str, role: str, title: str,
                  description: str) -> None
```

```python
# Don't type hint disnake.Role for the role parameter
@bot.slash_command(name="rr")
async def reactionrole(inter, emoji: str = commands.Param(), role: str = commands.Param(),
                       title: str = commands.Param(), description: str = commands.Param()):
    await dpys.rr.command(inter, emoji, role, title, description)
```

<br>

Command To List Reaction Roles:

```python
async def display(inter: ApplicationCommandInteraction) -> None
```

```python
@bot.slash_command(name="listrr")
async def listrr(inter: disnake.ApplicationCommandInteraction):
    await dpys.rr.display(inter)
```

<br>

On Raw Reaction Add Event Listener:

```python
async def add(payload: disnake.RawReactionActionEvent, bot: commands.Bot) -> None
```

```python
@bot.listen('on_raw_reaction_add')
async def rr_add(payload: disnake.RawReactionActionEvent):
    await dpys.rr.add(payload, bot)
```

<br>

On Raw Reaction Remove Event Listener:

```python
async def remove(payload: disnake.RawReactionActionEvent, bot: commands.Bot) -> None
```

```python
@bot.listen('on_raw_reaction_remove')
async def rr_remove(payload: disnake.RawReactionActionEvent):
    await dpys.rr.remove(payload, bot)
```

<br>

Clear Reaction Role command:

```python
async def clear_all(inter: disnake.ApplicationCommandInteraction) -> None


async def clear_one(inter: disnake.ApplicationCommandInteraction, message_id: int) -> None
```

```python
@bot.slash_command(name="rrclear")
async def rrclear(inter, id: str = commands.Param()):
    if id.lower() == "all":
        await dpys.rr.clear_all(inter)
    else:
        await dpys.rr.clear_one(inter, id)
```

<br>

Event Listeners To Clear Reaction Role Data:

```python
@bot.listen("on_message_delete")
async def rr_clear_on_message_delete(message: disnake.Message):
    await dpys.rr.clear_on_message_delete(message)


@bot.listen("on_raw_bulk_message_delete")
async def rr_clear_on_raw_bulk_message_delete(payload: disnake.RawBulkMessageDeleteEvent):
    await dpys.rr.clear_on_bulk_message_delete(payload)


@bot.listen("on_channel_delete")
async def rr_clear_on_channel_delete(channel: disnake.TextChannel):
    await dpys.rr.clear_on_channel_delete(channel)


@bot.listen("on_thread_delete")
async def rr_clear_on_thread_delete(thread: disnake.Thread):
    await dpys.rr.clear_on_thread_delete(thread)
```

<br>

## warnings Class

Warn:

```python
async def warn(inter: ApplicationCommandInteraction, member: discord.Member,
                   reason: typing.Optional[str] = None, expires: Optional[int] = -1) -> None:
```

```python
@bot.slash_command(name="warn")
async def warn(inter: disnake.ApplicationCommandInteraction, member: disnake.Member = commands.Param(),
               reason: str = commands.Param(default=None)):
    # Warning will expire in 1 day
    await dpys.warnings.warn(inter, member, reason, time.now() + 86400)
```

<br>

Unwarn:

```python
async def unwarn(inter: disnake.ApplicationCommandInteraction, member, dir, number: typing.Union[int, str]) -> bool
```

```python
# Pass in "all" as the number parameter to clear all warnings from a member
@bot.slash_command(name="unwarn")
async def unwarn(inter: disnake.ApplicationCommandInteraction, member: disnake.Member = commands.Param(),
                 number: str = commands.Param(default="all")):
    await dpys.warnings.unwarn(inter, member, number)
```

<br>

Punish:

```python
async def punish(inter: ApplicationCommandInteraction, member: discord.Member,
                 punishments: typing.Mapping[int, Punishment],
                 add_role: typing.Optional[int] = None, remove_role: typing.Optional[int] = None,
                 before: Optional[
                     Callable[[int, Punishment, discord.Member], Awaitable[Optional[Member]]]] = None) -> None:
```

```python
@bot.slash_command(name="warn")
async def warn(inter: disnake.ApplicationCommandInteraction, member: disnake.Member = commands.Param(),
               reason: str = commands.Param(default=None)):
    await dpys.warnings.warn(inter, member, reason)
    # This will do nothing for the first 2 warnings, but on the third warning it will kick the member.
    # Valid punishments for dpys.warnings.Punishment are kick, ban, mute, temp_ban, temp_mute, timeout
    # If you want to mute you have to pass in you mute role id and an optional mute remove role id.
    # For temporary punishments, a duration parameter can be passed into the dpys.warnings.Punishment constructor.
    # This is the number of seconds that the punishment will last.
    await dpys.warnings.punish(inter, member,
                               {3: dpys.warnings.Punishment("kick")})
```

<br>

If you want to use temp_ban or temp_mute, then include this cog in your bot.

```python
from disnake.ext import commands, tasks
import dpys

GET_MUTE_ROLE_ID = "an async function that takes in a guild id and returns the id for your mute role"
GET_MUTE_REMOVE_ROLE_ID = "an async function that takes in a guild id and returns the id for your mute remove role"


class DpysLoops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dpys_tempmute_loop.start()
        self.dpys_tempban_loop.start()

    @tasks.loop(seconds=1)
    async def dpys_tempmute_loop(self):
        await dpys.warnings.temp_mute_loop(self.bot, GET_MUTE_ROLE_ID, GET_MUTE_REMOVE_ROLE_ID)

    @dpys_tempmute_loop.before_loop
    async def before_dpys_tempmute_loop(self):
        await self.bot.wait_until_ready()
        
    @tasks.loop(minutes=30)
    async def dpys_expire(self):
        await dpys.warnings.expire_loop()
        
    @dpys_expire.before_loop
    async def before_dpys_tempmute_loop(self):
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

```python
async def warnings(inter: disnake.ApplicationCommandInteraction, member: disnake.Member, number: int = 0) -> None
```
The number is what warning you want to see. Set it to 0 to see the 5 most recent warnings.
```python
@bot.slash_command(name="warnings")
async def warnings(inter: disnake.ApplicationCommandInteraction, member: disnake.Member = commands.Param()):
    await dpys.warnings.warnings(inter, member)
```

<br>

```
warnings_list(guild: int, member_id: int)
```
Returns the actual list of warnings for a member

<br>

## curse Class

Add Word:

```python
async def add_banned_word(inter: disnake.ApplicationCommandInteraction, word: str) -> None
```

```python
@bot.slash_command(name="addword")
async def add_word(inter: disnake.ApplicationCommandInteraction, curses: str = commands.Param()):
    await dpys.curse.add_banned_word(inter, curses)
```

<br>

Remove Word:

```python
async def remove_banned_word(inter: disnake.ApplicationCommandInteraction, word: str) -> None
```

```python
@bot.slash_command(name="removeword")
async def remove_word(inter: disnake.ApplicationCommandInteraction, curses: str = commands.Param()):
    await dpys.curse.remove_banned_word(inter, curses)
```

<br>

Clear Words:

```python
async def clear_words(inter: disnake.ApplicationCommandInteraction) -> None
```

```python
@bot.slash_command(name="clearwords")
async def clear_words(inter: disnake.ApplicationCommandInteraction):
    await dpys.curse.clear_words(inter)
```

<br>

## misc Class

Reload:

```python
async def reload(inter: disnake.ApplicationCommandInteraction, bot: commands.Bot, cogs: typing.List[str]) -> None
```

```python
@bot.slash_command(name="reload")
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


