# This library is in development and bugs can be expected. If you encounter any bugs, want to give feedback, or would like to contribute, join our Discord server.
# https://jgltechnologies.com/dicord

"""
Copyright (c) 2021 JGL Technologies

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import contextlib
import os
import sqlite3
import time
from typing import *
import typing
import disnake as discord
import datetime
import aiosqlite
from disnake.ext import commands
from disnake import ApplicationCommandInteraction
from .utils import GuildData

RED = 0xD40C00
BLUE = 0x0000FF
GREEN = 0x32C12C
version = "5.5.6"
EPHEMERAL = True
warnings_db: aiosqlite.Connection
muted_db: aiosqlite.Connection
rr_db: aiosqlite.Connection
curse_db: aiosqlite.Connection

print("We recommend that you read https://jgltechnologies.com/dpys before you use DPYS.")


async def setup(bot: commands.BotBase, dir: str):
    global warnings_db, muted_db, rr_db, curse_db
    warnings_db = await aiosqlite.connect(os.path.join(dir, "warnings.db"))
    muted_db = await aiosqlite.connect(os.path.join(dir, "muted.db"))
    rr_db = await aiosqlite.connect(os.path.join(dir, "rr.db"))
    curse_db = await aiosqlite.connect(os.path.join(dir, "curse.db"))

    bot.warnings_db = warnings_db
    bot.muted_db = muted_db
    bot.rr_db = rr_db
    bot.curse_db = curse_db


class misc:

    @staticmethod
    async def reload(inter: ApplicationCommandInteraction, bot: commands.Bot, cogs: typing.List[str]) -> None:
        if not isinstance(cogs, list):
            raise Exception("cogs must be a list.")
        total = len(cogs)
        reloaded = 0
        for cog in cogs:
            try:
                bot.reload_extension(cog)
                reloaded += 1
            except:
                continue
        await inter.response.send_message(f"Successfully reloaded {reloaded}/{total} extensions.", ephemeral=EPHEMERAL)

    @staticmethod
    async def clear_data_on_guild_remove(guild: discord.Guild) -> None:
        with contextlib.suppress(sqlite3.Error):
            async with warnings_db.execute("DELETE FROM tempmute WHERE guild = ?", (str(guild.id),)):
                pass

        with contextlib.suppress(sqlite3.Error):
            async with warnings_db.execute("DELETE FROM tempban WHERE guild = ?", (str(guild.id),)):
                pass

        with contextlib.suppress(sqlite3.Error):
            async with warnings_db.execute("DELETE FROM warnings WHERE guild = ?", (str(guild.id),)):
                pass
        await warnings_db.commit()

        with contextlib.suppress(sqlite3.Error):
            async with rr_db.execute("DELETE FROM rr WHERE guild = ?", (str(guild.id),)):
                pass
        await rr_db.commit()

        with contextlib.suppress(sqlite3.Error):
            async with muted_db.execute("DELETE FROM muted WHERE guild = ?", (str(guild.id),)):
                pass
        await muted_db.commit()

        with contextlib.suppress(sqlite3.Error):
            async with curse_db.execute("DELETE FROM curses WHERE guild = ?", (str(guild.id),)):
                pass
        await curse_db.commit()


class admin:

    @staticmethod
    async def mute(inter: ApplicationCommandInteraction, member: discord.Member, role_add: int,
                   role_remove: typing.Optional[int] = None, reason: str = None, msg: str = None) -> None:
        if inter.guild.get_role(role_add) in member.roles:
            await inter.response.send_message(f"{member.name}#{member.discriminator} is already muted.",
                                              ephemeral=EPHEMERAL)
            return
        if len(str(reason)) > 256:
            reason = reason[:256]
        if not isinstance(inter.guild.get_role(role_add), discord.Role):
            return
        await member.add_roles(inter.guild.get_role(role_add))
        if role_remove is not None:
            with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                await member.remove_roles(inter.guild.get_role(role_remove))
        if reason is None:
            await inter.response.send_message(msg or f"Muted {str(member)}.", ephemeral=EPHEMERAL)
        else:
            await inter.response.send_message(
                msg or f"Muted {member.name}#{member.discriminator}. Reason: {reason}",
                ephemeral=EPHEMERAL)

    @staticmethod
    async def unmute(inter: ApplicationCommandInteraction, member: discord.Member, role_remove: int,
                     role_add: typing.Optional[int] = None, msg: str = None) -> bool:
        if inter.guild.get_role(role_remove) not in member.roles:
            await inter.response.send_message(f"{member.name}#{member.discriminator} is not muted.",
                                              ephemeral=EPHEMERAL)
            return False
        else:
            if not isinstance(inter.guild.get_role(role_remove), discord.Role):
                return False
            await member.remove_roles(inter.guild.get_role(role_remove))
            if role_add is not None:
                with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                    await member.add_roles(inter.guild.get_role(role_add))
            await inter.response.send_message(msg or f"Unmuted {member.name}#{member.discriminator}.",
                                              ephemeral=EPHEMERAL)
            return True

    @staticmethod
    async def clear(inter: ApplicationCommandInteraction, amount: typing.Optional[int] = 99999999999999999,
                    msg: str = None) -> int:
        limit = datetime.datetime.now() - datetime.timedelta(weeks=2)
        purged = await inter.channel.purge(limit=amount, after=limit)
        purged = len(purged)
        if purged != 1:
            message = msg or f"Cleared {purged} messages."
        else:
            message = msg or f"Cleared {purged} message."
        await inter.response.send_message(message, ephemeral=EPHEMERAL)
        return purged

    @staticmethod
    async def kick(inter: ApplicationCommandInteraction, member: discord.Member,
                   reason: typing.Optional[str] = None, msg: str = None) -> None:
        if len(str(reason)) > 256:
            reason = reason[:256]
        await member.kick(reason=reason)
        if reason is None:
            message = msg or f"Kicked {member.name}#{member.discriminator}."
        else:
            message = msg or f"Kicked {member.name}#{member.discriminator}. Reason: {reason}"
        await inter.response.send_message(message, ephemeral=EPHEMERAL)

    @staticmethod
    async def ban(inter: ApplicationCommandInteraction, member: discord.Member,
                  reason: typing.Optional[str] = None, msg: str = None) -> None:
        if len(str(reason)) > 256:
            reason = reason[:256]
        await member.ban(reason=reason)
        if reason is None:
            message = msg or f"Banned {member.name}#{member.discriminator}."
        else:
            message = msg or f"Banned {member.name}#{member.discriminator}. Reason: {reason}"
        await inter.response.send_message(message, ephemeral=EPHEMERAL)

    @staticmethod
    async def timeout(inter: ApplicationCommandInteraction, member: discord.Member,
                      duration: Union[float, datetime.timedelta] = None, until: datetime.datetime = None,
                      reason: typing.Optional[str] = None, msg: str = None) -> None:
        if len(str(reason)) > 256:
            reason = reason[:256]
        if duration is not None:
            await member.timeout(duration=duration, reason=reason)
            if isinstance(duration, datetime.timedelta):
                end_timeout = utils.get_discord_date((datetime.datetime.now() + duration).timestamp())
            else:
                end_timeout = utils.get_discord_date(
                    (datetime.datetime.now() + datetime.timedelta(seconds=duration)).timestamp())
        elif until is not None:
            await member.timeout(until=until, reason=reason)
            end_timeout = utils.get_discord_date(until.timestamp())
        else:
            await member.timeout(reason=reason)
            await inter.response.send_message(f"Removed timeout from {str(member)}.", ephemeral=EPHEMERAL)
            return
        if reason is None:
            message = msg or f"Timed out {str(member)} until {end_timeout}."
        else:
            message = msg or f"Timed out {str(member)} until {end_timeout}. Reason: {reason}"
        await inter.response.send_message(message, ephemeral=EPHEMERAL)

    @staticmethod
    async def softban(inter: ApplicationCommandInteraction, member: discord.Member,
                      reason: typing.Optional[str] = None, msg: str = None) -> None:
        if len(str(reason)) > 256:
            reason = reason[:256]
        await member.ban(reason=reason)
        if reason is None:
            message = msg or f"Soft banned {member.name}#{member.discriminator}."
        else:
            message = msg or f"Soft banned {member.name}#{member.discriminator}. Reason: {reason}"
        await inter.response.send_message(message, ephemeral=EPHEMERAL)
        await member.unban()

    @staticmethod
    async def unban(inter: ApplicationCommandInteraction, member: typing.Union[str, int], msg: str = None) -> bool:
        bans = inter.guild.bans()
        if isinstance(member, int):
            ban = [ban async for ban in bans if ban.user.id == member]
        else:
            try:
                name, discrim = member.split("#")
            except ValueError:
                raise commands.errors.UserNotFound(member)
            ban = [ban async for ban in bans if ban.user.discriminator ==
                   discrim and ban.user.name == name]
        if not ban:
            await inter.response.send_message(f"{member} is not banned.", ephemeral=EPHEMERAL)
            return False
        await inter.guild.unban(ban[0].user)
        await inter.response.send_message(msg or f"Unbanned {member}.", ephemeral=EPHEMERAL)
        return True


class curse:

    @staticmethod
    async def add_banned_word(inter: ApplicationCommandInteraction, word: str) -> None:
        word = word.lower()
        guildid = str(inter.guild.id)
        db = curse_db
        async with db.execute(f"""CREATE TABLE if NOT EXISTS curses(
        curse TEXT,
        guild TEXT,
        PRIMARY KEY (curse,guild)
        )"""):
            pass
        await db.commit()
        words = word.replace(" ", "")
        words = words.split(",")
        words = set(words)
        curses = await GuildData.curse_set(inter.guild.id, db)
        for x in words:
            if x in curses:
                msg = f"{x} is already banned."
                await inter.response.send_message(msg, ephemeral=EPHEMERAL)
                return
        for x in words:
            async with db.execute("INSERT INTO curses (curse,guild) VALUES (?,?)", (x, guildid)):
                pass
        await db.commit()
        await inter.response.send_message("Those words have been banned.", ephemeral=EPHEMERAL)

    @staticmethod
    async def remove_banned_word(inter: ApplicationCommandInteraction, word: str) -> None:
        db = curse_db
        guildid = str(inter.guild.id)
        try:
            word = word.lower()
            word = word.replace(" ", "")
            word = word.split(",")
            async with db.execute("SELECT curse FROM curses WHERE guild = ?", (guildid,)) as cursor:
                in_db = False
                async for entry in cursor:
                    curse = entry[0]
                    for x in word:
                        if x == curse:
                            in_db = True
            if not in_db:
                if len(word) > 1:
                    msg = "Those words are not banned."
                else:
                    msg = "That word is not banned."
                await inter.response.send_message(msg, ephemeral=EPHEMERAL)
                return
            for x in word:
                async with db.execute("DELETE FROM curses WHERE curse = ? and guild = ?", (x, guildid)):
                    pass
            await db.commit()
            await inter.response.send_message("Those words have been unbanned.", ephemeral=EPHEMERAL)
        except:
            await inter.response.send_message("Those words are not banned.", ephemeral=EPHEMERAL)

    @staticmethod
    async def message_filter(message: discord.Message,
                             exempt_roles: typing.Optional[typing.List[int]] = None) -> None:
        if message.author.bot or message.guild is None:
            return
        guildid = str(message.guild.id)
        if exempt_roles is not None:
            for id in exempt_roles:
                role = message.guild.get_role(id)
                if role in message.author.roles or message.author.top_role.position > role.position or message.author.bot:
                    return
            else:
                try:
                    messagecontent = message.content.lower()
                    db = curse_db
                    async with db.execute("SELECT curse FROM curses WHERE guild = ?", (guildid,)) as cursor:
                        async for entry in cursor:
                            if entry[0] in messagecontent.split():
                                await message.delete()
                                await message.channel.send("Do not say that here!", delete_after=5)
                except:
                    return

        else:
            try:
                messagecontent = message.content.lower()
                db = curse_db
                async with db.execute("SELECT curse FROM curses WHERE guild = ?", (guildid,)) as cursor:
                    async for entry in cursor:
                        if entry[0] in messagecontent.split():
                            await message.delete()
                            await message.channel.send("Do not say that here!", delete_after=5)
            except:
                return

    @staticmethod
    async def message_edit_filter(after: discord.Message,
                                  exempt_roles: typing.Optional[typing.List[int]] = None) -> None:
        message = after
        if message.author.bot or message.guild is None:
            return
        guildid = str(message.guild.id)
        if message.author.bot:
            return
        else:
            if exempt_roles is not None:
                for id in exempt_roles:
                    role = message.guild.get_role(id)
                    if role in message.author.roles or message.author.top_role.position > role.position or message.author.bot:
                        return
                else:
                    try:
                        messagecontent = message.content.lower()
                        db = curse_db
                        async with db.execute("SELECT curse FROM curses WHERE guild = ?", (guildid,)) as cursor:
                            async for entry in cursor:
                                if entry[0] in messagecontent.split():
                                    await message.delete()
                                    await message.channel.send("Do not say that here!", delete_after=5)
                    except:
                        return

            else:
                try:
                    messagecontent = message.content.lower()
                    db = curse_db
                    async with db.execute("SELECT curse FROM curses WHERE guild = ?", (guildid,)) as cursor:
                        async for entry in cursor:
                            if entry[0] in messagecontent.split():
                                await message.delete()
                                await message.channel.send("Do not say that here!", delete_after=5)
                except:
                    return

    @staticmethod
    async def clear_words(inter: ApplicationCommandInteraction) -> None:
        guildid = str(inter.guild.id)
        try:
            db = curse_db
            async with db.execute("DELETE FROM curses WHERE guild = ?", (guildid,)):
                pass
            await db.commit()
            await inter.response.send_message("Unbanned all words from this server.", ephemeral=EPHEMERAL)
        except:
            msg = "There are no banned words on this server."
            await inter.response.send_message(msg, ephemeral=EPHEMERAL)


class mute_on_join:

    @staticmethod
    async def mute_add(guild: discord.Guild, member: discord.Member) -> None:
        guildid = str(guild.id)
        member = str(member.id)
        db = muted_db
        async with db.execute(f"""CREATE TABLE if NOT EXISTS muted(
        name TEXT,
        guild TEXT,
        PRIMARY KEY (name,guild)
        )"""):
            pass
        await db.commit()
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("INSERT INTO muted (name,guild) VALUES (?,?)", (member, guildid)):
                pass
            await db.commit()

    @staticmethod
    async def mute_remove(guild: discord.Guild, member: discord.Member) -> None:
        member = str(member.id)
        guildid = str(guild.id)
        db = muted_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("DELETE FROM muted WHERE name = ? and guild = ?", (member, guildid)):
                pass
            await db.commit()

    @staticmethod
    async def mute_on_join(member: discord.Member, role: int) -> None:
        user = member
        guildid = str(member.guild.id)
        muted_role = member.guild.get_role(role)
        if not isinstance(muted_role, discord.Role):
            return
        member = str(member.id)
        db = muted_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT name FROM muted WHERE guild = ?", (guildid,)) as cursor:
                async for entry in cursor:
                    if entry[0] == member:
                        with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                            await user.add_roles(muted_role)

    @staticmethod
    async def manual_unmute_check(after: discord.Member, roleid: int) -> None:
        if after.bot:
            return
        db = muted_db
        guildid = str(after.guild.id)
        role = after.guild.get_role(roleid)
        memberid = str(after.id)
        with contextlib.suppress(sqlite3.Error):
            if role not in after.roles:
                async with db.execute("DELETE FROM muted WHERE guild = ? and name = ?", (guildid, memberid)):
                    pass
                await db.commit()


class warnings:
    class Punishment:
        def __init__(self, punishment: str, duration: typing.Optional[int] = None):
            if (punishment.startswith("temp") or punishment == "timeout") and duration is None:
                raise Exception("duration cannot be None for temporary punishments.")
            if punishment not in ["temp_ban", "temp_mute", "mute", "ban", "kick", "timeout"]:
                raise Exception("Invalid punishment.")
            self.punishment = punishment
            if not punishment.startswith("temp"):
                self.duration = None
            else:
                self.duration = duration

    @staticmethod
    async def warn(inter: ApplicationCommandInteraction, member: discord.Member,
                   reason: typing.Optional[str] = None, expires: Optional[int] = -1) -> None:
        db = warnings_db
        if len(str(reason)) > 256:
            reason = reason[:256]
        reason_str = str(reason)
        guildid = str(inter.guild.id)
        user = member
        member = str(member.id)
        async with db.execute("""CREATE TABLE if NOT EXISTS warnings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id TEXT,
        guild TEXT,
        reason TEXT,
        expires INTEGER
        )"""):
            pass
        await db.commit()
        async with db.execute("INSERT INTO warnings (member_id,guild,reason,expires) VALUES (?,?,?,?)",
                              (member, guildid, reason_str, expires)):
            pass
        await db.commit()
        if reason is None:
            msg = f"Warned {user.name}#{user.discriminator}."
        else:
            msg = f"Warned {user.name}#{user.discriminator}. Reason: {reason}"
        await inter.response.send_message(msg, ephemeral=EPHEMERAL)

    @staticmethod
    async def warnings_list(inter: ApplicationCommandInteraction, member: discord.Member) -> None:
        guildid = str(inter.guild.id)
        user = member
        member = str(member.id)
        db = warnings_db
        try:
            async with db.execute("SELECT reason FROM warnings WHERE guild = ? and member_id = ?",
                                  (guildid, member)) as cursor:
                embed = discord.Embed(
                    color=BLUE, title=f"{user.name}#{user.discriminator}'s 5 Most Recent Warnings")
                number = 0
                async for entry in cursor:
                    number += 1
                    if number < 6:
                        embed.add_field(
                            name=f"#{number} warning",
                            value=f"Reason: {entry[0]}",
                            inline=False)
                if number > 0:
                    embed.set_footer(text=f"Total Warnings | {number}")
                    await inter.response.send_message(embed=embed, ephemeral=EPHEMERAL)
                else:
                    await inter.response.send_message(f"{user.name}#{user.discriminator} has no warnings.",
                                                      ephemeral=EPHEMERAL)
        except:
            await inter.response.send_message(f"{user.name}#{user.discriminator} has no warnings.", ephemeral=EPHEMERAL)

    @staticmethod
    async def unwarn(inter: ApplicationCommandInteraction, member, number: typing.Union[int, str]) -> bool:
        user = member
        guild = str(inter.guild.id)
        member = str(member.id)
        number = str(number)
        number = number.lower()
        db = warnings_db
        try:
            async with db.execute("SELECT reason FROM warnings WHERE guild = ? and member_id = ?",
                                  (guild, member)) as cursor:
                count = 0
                async for _ in cursor:
                    count += 1
        except:
            msg = f"{user.name}#{user.discriminator} has no warnings."
            await inter.response.send_message(msg, ephemeral=EPHEMERAL)
            return False
        if count < 1:
            msg = f"{user.name}#{user.discriminator} has no warnings."
            await inter.response.send_message(msg, ephemeral=EPHEMERAL)
            return False
        if number == "all":
            async with db.execute("DELETE FROM warnings WHERE guild = ? and member_id = ?", (guild, member)):
                pass
            await db.commit()
            msg = f"Cleared all warnings from {user.name}#{user.discriminator}."
            await inter.response.send_message(msg, ephemeral=EPHEMERAL)
            return True
        else:
            try:
                if "," in number:
                    number = number.replace(" ", "")
                    number_list = number.split(",")
                    number_list = list(map(int, number_list))
                    number_list = sorted(number_list, reverse=True)
                    dict = {}
                    async with db.execute(
                            "SELECT id,row_number() OVER (ORDER BY id) FROM warnings WHERE guild = ? and member_id = ?",
                            (guild, member)) as cursor:
                        async for entry in cursor:
                            id, pos = entry
                            pos = str(pos)
                            dict.update({pos: id})
                    for x in number_list:
                        async with db.execute("DELETE FROM warnings WHERE id = ?", (dict[str(x)],)):
                            pass
                    await db.commit()
                    number_list = list(map(str, number_list))
                    number_list = ", ".join(number_list)
                    await inter.response.send_message(f"Cleared warnings {number_list} from {str(user)}.",
                                                      ephemeral=EPHEMERAL)
                else:
                    number = int(number)
                    dict = {}
                    async with db.execute(
                            "SELECT id,row_number() OVER (ORDER BY id) FROM warnings WHERE guild = ? and member_id = ?",
                            (guild, member)) as cursor:
                        async for entry in cursor:
                            id, pos = entry
                            pos = str(pos)
                            dict.update({pos: id})
                    async with db.execute("DELETE FROM warnings WHERE id = ?", (dict[str(number)],)):
                        pass
                    await db.commit()
                    msg = f"Cleared {user.name}#{user.discriminator}'s #{number} warning."
                    await inter.response.send_message(msg, ephemeral=EPHEMERAL)
                    return True
            except:
                if number == "all":
                    msg = f"{user.name}#{user.discriminator} has no warnings."
                else:
                    msg = f"{user.name}#{user.discriminator} does not have that many warnings."
                await inter.response.send_message(msg, ephemeral=EPHEMERAL)
                return False

    @staticmethod
    async def punish(inter: ApplicationCommandInteraction, member: discord.Member,
                     punishments: typing.Mapping[int, Punishment],
                     add_role: typing.Optional[int] = None, remove_role: typing.Optional[int] = None,
                     before: Optional[Callable[
                         [int, Punishment, discord.Member], Awaitable[Optional[discord.Message]]]] = None) -> None:
        memberid = str(member.id)
        guild = str(inter.guild.id)
        db = warnings_db
        async with db.execute("""CREATE TABLE IF NOT EXISTS tempmute(
                    guild TEXT,
                    member TEXT,
                    time DATETIME
                    )"""):
            pass
        async with db.execute("""CREATE TABLE IF NOT EXISTS tempban(
                    guild TEXT,
                    member TEXT,
                    time DATETIME
                    )"""):
            pass
        await db.commit()
        try:
            async with db.execute("SELECT reason FROM warnings WHERE guild = ? and member_id = ?",
                                  (guild, memberid)) as cursor:
                warnings_number = 0
                async for _ in cursor:
                    warnings_number += 1
        except:
            return
        if warnings_number not in punishments:
            return
        if punishments[warnings_number].duration is not None:
            if punishments[warnings_number].punishment == "temp_ban":
                msg = await before(warnings_number, punishments[warnings_number], member)
                time = punishments[warnings_number].duration
                try:
                    await member.ban(reason=f"You have received {warnings_number} warning(s).")
                except (discord.Forbidden, discord.HTTPException) as e:
                    with contextlib.suppress(Exception):
                        await msg.delete()
                    raise e
                time = datetime.datetime.now() + datetime.timedelta(seconds=time)
                async with db.execute("INSERT INTO tempban (guild,member,time) VALUES (?,?,?)",
                                      (guild, memberid, time)):
                    pass
                await db.commit()
                return
            elif punishments[warnings_number].punishment == "temp_mute":
                add_role = inter.guild.get_role(add_role)
                if not isinstance(add_role, discord.Role):
                    return
                remove_role = inter.guild.get_role(remove_role)
                if add_role in member.roles:
                    return
                else:
                    time = punishments[warnings_number].duration
                    if add_role is not None:
                        await member.add_roles(add_role)
                    if remove_role is not None:
                        await member.remove_roles(remove_role)
                    await mute_on_join.mute_add(inter.guild, member)
                    time = datetime.datetime.now() + datetime.timedelta(seconds=time)
                    async with db.execute("INSERT INTO tempmute (guild,member,time) VALUES (?,?,?)",
                                          (guild, memberid, time)):
                        pass
                    await db.commit()
                    await before(warnings_number, punishments[warnings_number], member)
            else:
                time = punishments[warnings_number].duration
                await member.timeout(reason=f"You have received {warnings_number} warning(s).", duration=time)
                await before(warnings_number, punishments[warnings_number], member)
                return
        else:
            if punishments[warnings_number].punishment == "ban":
                msg = await before(warnings_number, punishments[warnings_number], member)
                try:
                    await member.ban(reason=f"You have received {warnings_number} warning(s).")
                except (discord.Forbidden, discord.HTTPException) as e:
                    with contextlib.suppress(Exception):
                        await msg.delete()
                    raise e
                return
            if punishments[warnings_number].punishment == "kick":
                msg = await before(warnings_number, punishments[warnings_number], member)
                try:
                    await member.kick(reason=f"You have received {warnings_number} warning(s).")
                except (discord.Forbidden, discord.HTTPException) as e:
                    with contextlib.suppress(Exception):
                        await msg.delete()
                    raise e
                return
            if punishments[warnings_number].punishment == "mute":
                add_role = inter.guild.get_role(add_role)
                remove_role = inter.guild.get_role(remove_role)
                if not isinstance(add_role, discord.Role):
                    return
                if remove_role is not None:
                    await member.remove_roles(remove_role)
                if add_role is not None:
                    await member.add_roles(add_role)
                await mute_on_join.mute_add(inter.guild, member)
                await before(warnings_number, punishments[warnings_number], member)

    @staticmethod
    async def temp_mute_loop(bot: commands.Bot, add_role_func: Callable[[int], Awaitable[Optional[int]]],
                             remove_role_func: Optional[Callable[[int], Awaitable[Optional[int]]]] = None) -> None:
        db = warnings_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT guild,member,time FROM tempmute") as cursor:
                async for entry in cursor:
                    guild_id, member_id, time_str = entry
                    guild = bot.get_guild(int(guild_id))
                    if not isinstance(guild, discord.Guild):
                        async with db.execute("DELETE FROM tempmute WHERE guild = ?", (str(guild_id),)):
                            pass
                        continue
                    member = guild.get_member(int(member_id))
                    if not isinstance(member, discord.Member):
                        async with db.execute("DELETE FROM tempmute WHERE guild = ? and member = ?",
                                              (str(guild_id), str(member_id))):
                            pass
                        continue
                    time = datetime.datetime.fromisoformat(time_str)
                    role_add = await add_role_func(int(guild_id))
                    if remove_role_func is None:
                        role_remove = None
                    else:
                        role_remove = await remove_role_func(int(guild_id))
                    if datetime.datetime.now() >= time:
                        with contextlib.suppress(Exception):
                            await member.add_roles(guild.get_role(int(role_remove)))
                        with contextlib.suppress(Exception):
                            await member.remove_roles(guild.get_role(int(role_add)))
                        with contextlib.suppress(sqlite3.Error):
                            async with db.execute("DELETE FROM tempmute WHERE guild = ? and member = ? and time = ?",
                                                  (str(guild.id), str(member.id), time_str)):
                                pass
                        await mute_on_join.mute_remove(guild, member)
            await db.commit()

    @staticmethod
    async def temp_ban_loop(bot: commands.Bot) -> None:
        db = warnings_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT guild,member,time FROM tempban") as cursor:
                async for entry in cursor:
                    guild_id, member, time_str = entry
                    guild = bot.get_guild(int(guild_id))
                    if not isinstance(guild, discord.Guild):
                        async with db.execute("DELETE FROM tempban WHERE guild = ?", (str(guild_id),)):
                            pass
                        continue
                    time = datetime.datetime.fromisoformat(time_str)
                    if datetime.datetime.now() >= time:
                        async with db.execute("DELETE FROM tempban WHERE guild = ? and member = ? and time = ?",
                                              (str(guild.id), str(member), time_str)):
                            pass
                        with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                            await guild.unban(discord.Object(id=int(member)))
                await db.commit()

    @staticmethod
    async def expire_loop() -> None:
        db = warnings_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT id,expires FROM warnings") as cursor:
                async for entry in cursor:
                    id, expires = entry
                    if expires == -1:
                        continue
                    if time.time() >= expires:
                        async with db.execute("DELETE FROM warnings WHERE id=?", (id,)):
                            pass
                await db.commit()



class rr:

    @staticmethod
    async def command(inter: ApplicationCommandInteraction, emoji: str, role: str, title: str,
                      description: str) -> None:
        db = rr_db
        await inter.response.send_message("Attempting to create reaction role...", ephemeral=EPHEMERAL)
        async with db.execute("""CREATE TABLE IF NOT EXISTS rr(
        msg_id TEXT,
        emoji UNICODE,
        role TEXT,
        guild TEXT,
        channel TEXT
        )"""):
            pass
        await db.commit()
        embed = discord.Embed(
            title=title,
            color=BLUE,
            description=description)
        if "," in emoji:
            emoji = emoji.replace(" ", "")
            emoji_list = emoji.split(",")
            role = role.replace(" ", "")
            role_list = role.split(",")
            if len(role_list) != len(emoji_list):
                await inter.followup.send("Emoji list must be same length as role list.",
                                          ephemeral=EPHEMERAL)
                return
            for role in role_list:
                role = role.replace("<", "")
                role = role.replace(">", "")
                role = role.replace("@", "")
                role = role.replace("&", "")
                try:
                    if inter.guild.get_role(int(role)) is None:
                        await inter.followup.send("Invalid role", ephemeral=EPHEMERAL)
                        return
                except:
                    await inter.followup.send("Invalid role", ephemeral=EPHEMERAL)
                    return
            msg = await inter.channel.send(embed=embed)
            number = 0
            for x in emoji_list:
                role = role_list[number]
                if "@" not in role:
                    await inter.followup.send("Invalid role", ephemeral=EPHEMERAL)
                    await msg.delete()
                    return
                role = role.replace("<", "")
                role = role.replace(">", "")
                role = role.replace("@", "")
                role = role.replace("&", "")
                number += 1
                await msg.add_reaction(x)
                async with db.execute("INSERT INTO rr (msg_id,emoji,role,guild,channel) VALUES (?,?,?,?,?)",
                                      (str(msg.id), x, str(role), str(inter.guild.id), str(inter.channel.id))):
                    pass
            await inter.followup.send("Successfully created the reaction role.", ephemeral=EPHEMERAL)
            await db.commit()
        else:
            if "@" not in role:
                await inter.followup.send("Invalid role", ephemeral=EPHEMERAL)
                return
            role = role.replace("<", "")
            role = role.replace(">", "")
            role = role.replace("@", "")
            role = role.replace("&", "")
            try:
                if inter.guild.get_role(int(role)) is None:
                    await inter.followup.send("Invalid role", ephemeral=EPHEMERAL)
                    return
            except:
                await inter.followup.send("Invalid role", ephemeral=EPHEMERAL)
                return
            msg = await inter.channel.send(embed=embed)
            await msg.add_reaction(emoji)
            async with db.execute("INSERT INTO rr (msg_id,emoji,role,guild,channel) VALUES (?,?,?,?,?)",
                                  (str(msg.id), emoji, str(role), str(inter.guild.id), str(inter.channel.id))):
                pass
            await db.commit()
            await inter.followup.send("Successfully created the reaction role.", ephemeral=EPHEMERAL)

    @staticmethod
    async def add(payload: discord.RawReactionActionEvent, bot: commands.Bot) -> None:
        if payload.guild_id is None:
            return
        if payload.member.bot:
            return
        db = rr_db
        guild = bot.get_guild(payload.guild_id)
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT emoji,role FROM rr WHERE guild = ? and msg_id = ?",
                                  (str(guild.id), str(payload.message_id))) as cursor:
                async for entry in cursor:
                    emoji, role = entry
                    role = guild.get_role(int(role))
                    if str(payload.emoji) == emoji:
                        with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                            await payload.member.add_roles(role)

    @staticmethod
    async def remove(payload: discord.RawReactionActionEvent, bot: commands.Bot) -> None:
        if payload.guild_id is None:
            return
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member.bot:
            return
        db = rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT emoji,role FROM rr WHERE guild = ? and msg_id = ?",
                                  (str(guild.id), str(payload.message_id))) as cursor:
                async for entry in cursor:
                    emoji, role = entry
                    role = guild.get_role(int(role))
                    if str(payload.emoji) == emoji:
                        with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                            await member.remove_roles(role)

    @staticmethod
    async def clear_all(inter: ApplicationCommandInteraction) -> None:
        guild = str(inter.guild.id)
        db = rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("DELETE FROM rr WHERE guild = ?", (guild,)):
                pass
            await db.commit()
        msg = "Deleted all reaction role info for this server."
        await inter.response.send_message(msg, ephemeral=EPHEMERAL)

    @staticmethod
    async def clear_one(inter: ApplicationCommandInteraction, message_id: int) -> None:
        guild = str(inter.guild.id)
        message_id = str(message_id)
        db = rr_db
        message_id = message_id.replace(" ", "")
        message_id = message_id.split(",")
        for x in message_id:
            try:
                async with db.execute("DELETE FROM rr WHERE guild = ? and msg_id = ?", (guild, x)):
                    pass
            except:
                break
        await db.commit()
        message_id = ", ".join(message_id)
        msg = f"Deleted all reaction role info with message ID(s): {message_id}"
        await inter.response.send_message(msg, ephemeral=EPHEMERAL)

    @staticmethod
    async def clear_on_message_delete(message: discord.Message) -> None:
        if message.guild is None:
            return
        db = rr_db
        guild = str(message.guild.id)
        id = str(message.id)
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT msg_id FROM rr WHERE guild = ?", (guild,)) as cursor:
                async for entry in cursor:
                    msg_id = entry[0]
                    if msg_id == id:
                        async with db.execute("DELETE FROM rr WHERE msg_id = ? and guild = ?", (msg_id, guild)):
                            pass
                        break
                await db.commit()

    @staticmethod
    async def clear_on_channel_delete(channel: discord.TextChannel) -> None:
        channel_id = channel.id
        guild = channel.guild.id
        db = rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT channel FROM rr WHERE guild = ?", (str(guild),)) as cursor:
                async for entry in cursor:
                    channel = int(entry[0])
                    if channel == channel_id:
                        async with db.execute("DELETE FROM rr WHERE guild = ? and channel = ?",
                                              (str(guild), str(channel))):
                            pass
                        break
                await db.commit()

    @staticmethod
    async def clear_on_thread_delete(thread: discord.Thread) -> None:
        thread_id = thread.id
        guild = thread.guild.id
        db = rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT channel FROM rr WHERE guild = ?", (str(guild),)) as cursor:
                async for entry in cursor:
                    channel = int(entry[0])
                    if channel == thread_id:
                        async with db.execute("DELETE FROM rr WHERE guild = ? and channel = ?",
                                              (str(guild), str(channel))):
                            pass
                        break
                await db.commit()

    @staticmethod
    async def clear_on_bulk_message_delete(payload: discord.RawBulkMessageDeleteEvent) -> None:
        ids = payload.message_ids
        guild = payload.guild_id
        if guild is None:
            return
        db = rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT msg_id FROM rr WHERE guild = ?", (str(guild),)) as cursor:
                async for entry in cursor:
                    msg_id = int(entry[0])
                    for id in ids:
                        if id == msg_id:
                            async with db.execute("DELETE FROM rr WHERE guild = ? and msg_id = ?",
                                                  (str(guild), str(msg_id))):
                                pass
                        break
                    break
            await db.commit()

    @staticmethod
    async def display(inter: ApplicationCommandInteraction) -> None:
        guild = str(inter.guild.id)
        db = rr_db
        embed = discord.Embed(title="5 Most Recent Reaction Roles", color=BLUE)
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT msg_id FROM rr WHERE guild = ? GROUP BY msg_id", (guild,)) as cursor:
                number = 0
                async for entry in cursor:
                    async with db.execute(
                            "SELECT role,emoji,channel,msg_id FROM rr WHERE guild = ? and msg_id = ?",
                            (guild, entry[0])) as f:
                        msg = ""
                        msg_limit = ""
                        async for entry in f:
                            role, emoji, channel, msg_id = entry
                            channel = inter.guild.get_channel(
                                int(channel))
                            role = inter.guild.get_role(int(role))
                            try:
                                role = f"@{role.name}"
                            except:
                                role = "@deleted-role"
                            try:
                                channel = f"#{channel.name}"
                            except:
                                channel = "#deleted-channel"
                            msg += f"Emoji: {emoji} Role: {role}\n"
                        msg_limit += f"Channel: {channel} \nMessage ID: {msg_id}\n"
                        msg += f"Channel: {channel} \nMessage ID: {msg_id}\n"
                        number += 1
                    if number < 6:
                        if len(msg) > 1010:
                            embed.add_field(
                                name=f"Reaction Role #{number}", inline=False, value=msg_limit)
                        else:
                            embed.add_field(
                                name=f"Reaction Role #{number}", inline=False, value=msg)
            if number > 0:
                embed.set_footer(
                    text=f"Total Reaction Roles | {number}")
                await inter.response.send_message(embed=embed, ephemeral=EPHEMERAL)
            else:
                msg = "There are no reaction roles in this server."
                await inter.response.send_message(msg, ephemeral=EPHEMERAL)
