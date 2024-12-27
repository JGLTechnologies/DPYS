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
import math
import os
import sqlite3
import time
from typing import *
import typing
import disnake
import disnake as discord
import datetime
import aiosqlite
from disnake.ext import commands
from disnake import ApplicationCommandInteraction
from dpys.utils import ListScroller
import asyncio

from .utils import GuildData, get_discord_date

COLOR = None
version = "5.6.2"
EPHEMERAL = True
warnings_db: aiosqlite.Connection
muted_db: aiosqlite.Connection
rr_db: aiosqlite.Connection
curse_db: aiosqlite.Connection

print(
    "We recommend that you read https://jgltechnologies.com/dpys before you use DPYS."
)


async def setup(
    bot: commands.BotBase,
    dir: str,
    color: disnake.colour.Colour = discord.Colour.blurple(),
):
    global warnings_db, muted_db, rr_db, curse_db, COLOR
    warnings_db = await aiosqlite.connect(os.path.join(dir, "warnings.db"))
    muted_db = await aiosqlite.connect(os.path.join(dir, "muted.db"))
    rr_db = await aiosqlite.connect(os.path.join(dir, "rr.db"))
    curse_db = await aiosqlite.connect(os.path.join(dir, "curse.db"))
    COLOR = color
    bot.warnings_db = warnings_db
    bot.muted_db = muted_db
    bot.rr_db = rr_db
    bot.curse_db = curse_db


class misc:
    @staticmethod
    async def reload(
        inter: ApplicationCommandInteraction, bot: commands.Bot, cogs: typing.List[str]
    ) -> None:
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
        await inter.send(
            f"Successfully reloaded {reloaded}/{total} extensions.", ephemeral=EPHEMERAL
        )

    @staticmethod
    async def clear_data_on_guild_remove(guild: discord.Guild) -> None:
        with contextlib.suppress(sqlite3.Error):
            async with warnings_db.execute(
                "DELETE FROM tempmute WHERE guild = ?", (str(guild.id),)
            ):
                pass

        with contextlib.suppress(sqlite3.Error):
            async with warnings_db.execute(
                "DELETE FROM tempban WHERE guild = ?", (str(guild.id),)
            ):
                pass

        with contextlib.suppress(sqlite3.Error):
            async with warnings_db.execute(
                "DELETE FROM warnings WHERE guild = ?", (str(guild.id),)
            ):
                pass
        await warnings_db.commit()

        with contextlib.suppress(sqlite3.Error):
            async with rr_db.execute(
                "DELETE FROM rr WHERE guild = ?", (str(guild.id),)
            ):
                pass
        await rr_db.commit()

        with contextlib.suppress(sqlite3.Error):
            async with muted_db.execute(
                "DELETE FROM muted WHERE guild = ?", (str(guild.id),)
            ):
                pass
        await muted_db.commit()

        with contextlib.suppress(sqlite3.Error):
            async with curse_db.execute(
                "DELETE FROM curses WHERE guild = ?", (str(guild.id),)
            ):
                pass
        await curse_db.commit()


class admin:
    @staticmethod
    async def mute(
        inter: ApplicationCommandInteraction,
        member: discord.Member,
        role_add: int,
        role_remove: typing.Optional[int] = None,
        reason: str = None,
        msg: str = None,
    ) -> None:
        if inter.guild.get_role(role_add) in member.roles:
            await inter.send(
                f"{member.display_name} is already muted.", ephemeral=EPHEMERAL
            )
            return
        if len(str(reason)) > 256:
            reason = reason[:253] + "..."
        if not isinstance(inter.guild.get_role(role_add), discord.Role):
            return
        await member.add_roles(inter.guild.get_role(role_add))
        if role_remove is not None:
            with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                await member.remove_roles(inter.guild.get_role(role_remove))
        await member.edit(reason=reason, voice_channel=None)
        if reason is None:
            await inter.send(
                msg or f"Muted {member.display_name}.", ephemeral=EPHEMERAL
            )
        else:
            await inter.send(
                msg or f"Muted {member.display_name}. Reason: {reason}",
                ephemeral=EPHEMERAL,
            )

    @staticmethod
    async def unmute(
        inter: ApplicationCommandInteraction,
        member: discord.Member,
        role_remove: int,
        role_add: typing.Optional[int] = None,
        msg: str = None,
    ) -> bool:
        if inter.guild.get_role(role_remove) not in member.roles:
            await inter.send(
                f"{member.display_name} is not muted.", ephemeral=EPHEMERAL
            )
            return False
        else:
            if not isinstance(inter.guild.get_role(role_remove), discord.Role):
                return False
            await member.remove_roles(inter.guild.get_role(role_remove))
            if role_add is not None:
                with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                    await member.add_roles(inter.guild.get_role(role_add))
            await inter.send(
                msg or f"Unmuted {member.display_name}.", ephemeral=EPHEMERAL
            )
            return True

    @staticmethod
    async def clear(
        inter: ApplicationCommandInteraction,
        amount: typing.Optional[int] = 99999999999999999,
        msg: str = None,
    ) -> int:
        limit = datetime.datetime.now() - datetime.timedelta(weeks=2)
        purged = await inter.channel.purge(limit=amount, after=limit)
        purged = len(purged)
        if purged != 1:
            message = msg or f"Cleared {purged} messages."
        else:
            message = msg or f"Cleared {purged} message."
        await inter.send(message, ephemeral=EPHEMERAL)
        return purged

    @staticmethod
    async def kick(
        inter: ApplicationCommandInteraction,
        member: discord.Member,
        reason: typing.Optional[str] = None,
        msg: str = None,
    ) -> None:
        if len(str(reason)) > 256:
            reason = reason[:253] + "..."
        await member.kick(reason=reason)
        if reason is None:
            message = msg or f"Kicked {member.display_name}."
        else:
            message = msg or f"Kicked {member.display_name}. Reason: {reason}"
        await inter.send(message, ephemeral=EPHEMERAL)

    @staticmethod
    async def ban(
        inter: ApplicationCommandInteraction,
        member: discord.User,
        reason: typing.Optional[str] = None,
        msg: str = None,
    ) -> None:
        if len(str(reason)) > 256:
            reason = reason[:253] + "..."
        await inter.guild.ban(member, reason=reason)
        if reason is None:
            message = msg or f"Banned {member.display_name}."
        else:
            message = msg or f"Banned {member.display_name}. Reason: {reason}"
        await inter.send(message, ephemeral=EPHEMERAL)

    @staticmethod
    async def timeout(
        inter: ApplicationCommandInteraction,
        member: discord.Member,
        duration: Union[float, datetime.timedelta] = None,
        until: datetime.datetime = None,
        reason: typing.Optional[str] = None,
        msg: str = None,
    ) -> None:
        if len(str(reason)) > 256:
            reason = reason[:253] + "..."
        if duration is not None:
            await member.timeout(duration=duration, reason=reason)
            if isinstance(duration, datetime.timedelta):
                end_timeout = get_discord_date(
                    (datetime.datetime.now() + duration).timestamp()
                )
            else:
                end_timeout = get_discord_date(
                    (
                        datetime.datetime.now() + datetime.timedelta(seconds=duration)
                    ).timestamp()
                )
        elif until is not None:
            await member.timeout(until=until, reason=reason)
            end_timeout = get_discord_date(until.timestamp())
        else:
            await member.edit(timeout=None)
            await inter.send(
                f"Removed timeout from {member.display_name}.", ephemeral=EPHEMERAL
            )
            return
        if reason is None:
            message = msg or f"Timed out {member.display_name} until {end_timeout}."
        else:
            message = (
                msg
                or f"Timed out {member.display_name} until {end_timeout}. Reason: {reason}"
            )
        await inter.send(message, ephemeral=EPHEMERAL)

    @staticmethod
    async def softban(
        inter: ApplicationCommandInteraction,
        member: discord.Member,
        reason: typing.Optional[str] = None,
        msg: str = None,
    ) -> None:
        if len(str(reason)) > 256:
            reason = reason[:253] + "..."
        await member.ban(reason=reason)
        if reason is None:
            message = msg or f"Soft banned {member.display_name}."
        else:
            message = msg or f"Soft banned {member.display_name}. Reason: {reason}"
        await inter.send(message, ephemeral=EPHEMERAL)
        await member.unban()

    @staticmethod
    async def unban(
        inter: ApplicationCommandInteraction,
        member: discord.User,
        msg: str = None,
    ) -> bool:
        bans = inter.guild.bans()
        ban = [ban async for ban in bans if ban.user.id == member.id]
        if not ban:
            await inter.send(
                f"{member.display_name} is not banned.", ephemeral=EPHEMERAL
            )
            return False
        await inter.guild.unban(ban[0].user)
        await inter.send(
            msg or f"Unbanned {member.display_name}.", ephemeral=EPHEMERAL
        )
        return True


class curse:
    @staticmethod
    async def add_banned_word(inter: ApplicationCommandInteraction, word: str) -> None:
        word = word.lower()
        guildid = str(inter.guild.id)
        db = curse_db
        async with db.execute(
            f"""CREATE TABLE if NOT EXISTS curses(
        curse TEXT,
        guild TEXT,
        PRIMARY KEY (curse,guild)
        )"""
        ):
            pass
        await db.commit()
        words = word.replace(" ", "")
        words = words.split(",")
        words = set(words)
        curses = await GuildData.curse_set(inter.guild.id, db)
        for x in words:
            if x in curses:
                msg = f"{x} is already banned."
                await inter.send(msg, ephemeral=EPHEMERAL)
                return
        for x in words:
            async with db.execute(
                "INSERT INTO curses (curse,guild) VALUES (?,?)", (x, guildid)
            ):
                pass
        await db.commit()
        await inter.send(
            "Those words have been banned.", ephemeral=EPHEMERAL
        )

    @staticmethod
    async def remove_banned_word(
        inter: ApplicationCommandInteraction, word: str
    ) -> None:
        db = curse_db
        guildid = str(inter.guild.id)
        try:
            word = word.lower()
            word = word.replace(" ", "")
            word = word.split(",")
            async with db.execute(
                "SELECT curse FROM curses WHERE guild = ?", (guildid,)
            ) as cursor:
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
                await inter.send(msg, ephemeral=EPHEMERAL)
                return
            for x in word:
                async with db.execute(
                    "DELETE FROM curses WHERE curse = ? and guild = ?", (x, guildid)
                ):
                    pass
            await db.commit()
            await inter.send(
                "Those words have been unbanned.", ephemeral=EPHEMERAL
            )
        except:
            await inter.send(
                "Those words are not banned.", ephemeral=EPHEMERAL
            )

    @staticmethod
    async def message_filter(
        message: discord.Message, exempt_roles: typing.Optional[typing.List[int]] = None
    ) -> None:
        if message.author.bot or message.guild is None or message.author.guild_permissions.administrator:
            return
        guildid = str(message.guild.id)
        if exempt_roles is not None:
            for id in exempt_roles:
                role = message.guild.get_role(id)
                if role is not None:
                    if role in message.author.roles or message.author.top_role.position > role.position:
                        return
        try:
            messagecontent = message.content.lower()
            db = curse_db
            async with db.execute(
                "SELECT curse FROM curses WHERE guild = ?", (guildid,)
            ) as cursor:
                async for entry in cursor:
                    if entry[0] in messagecontent.split():
                        await message.delete()
                        await message.channel.send(
                            "Do not say that here!", delete_after=5
                        )
        except:
            return

    @staticmethod
    async def message_edit_filter(
        after: discord.Message, exempt_roles: typing.Optional[typing.List[int]] = None
    ) -> None:
        message = after
        if message.author.bot or message.guild is None or message.author.guild_permissions.administrator:
            return
        guildid = str(message.guild.id)
        if exempt_roles is not None:
            for id in exempt_roles:
                role = message.guild.get_role(id)
                if role is not None:
                    if role in message.author.roles or message.author.top_role.position > role.position:
                        return
        try:
            messagecontent = message.content.lower()
            db = curse_db
            async with db.execute(
                "SELECT curse FROM curses WHERE guild = ?", (guildid,)
            ) as cursor:
                async for entry in cursor:
                    if entry[0] in messagecontent.split():
                        await message.delete()
                        await message.channel.send(
                            "Do not say that here!", delete_after=5
                        )
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
            await inter.send(
                "Unbanned all words from this server.", ephemeral=EPHEMERAL
            )
        except:
            msg = "There are no banned words on this server."
            await inter.send(msg, ephemeral=EPHEMERAL)


class mute_on_join:
    @staticmethod
    async def mute_add(guild: discord.Guild, member: discord.Member) -> None:
        guildid = str(guild.id)
        member = str(member.id)
        db = muted_db
        async with db.execute(
            f"""CREATE TABLE if NOT EXISTS muted(
        name TEXT,
        guild TEXT,
        PRIMARY KEY (name,guild)
        )"""
        ):
            pass
        await db.commit()
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "INSERT INTO muted (name,guild) VALUES (?,?)", (member, guildid)
            ):
                pass
            await db.commit()

    @staticmethod
    async def mute_remove(guild: discord.Guild, member: discord.Member) -> None:
        member = str(member.id)
        guildid = str(guild.id)
        db = muted_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "DELETE FROM muted WHERE name = ? and guild = ?", (member, guildid)
            ):
                pass
            await db.commit()

    @staticmethod
    async def mute_on_join(
        member: discord.Member, role_add: int, role_remove: typing.Optional[int] = None
    ) -> None:
        guildid = str(member.guild.id)
        muted_role = member.guild.get_role(role_add)
        if not isinstance(muted_role, discord.Role):
            return
        db = muted_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT name FROM muted WHERE guild = ?", (guildid,)
            ) as cursor:
                async for entry in cursor:
                    if entry[0] == str(member.id):
                        with contextlib.suppress(
                            discord.Forbidden, discord.HTTPException
                        ):
                            await member.add_roles(muted_role)
                        if role_remove is not None:
                            with contextlib.suppress(
                                discord.Forbidden, discord.HTTPException
                            ):
                                await member.remove_roles(
                                    member.guild.get_role(role_remove)
                                )

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
                async with db.execute(
                    "DELETE FROM muted WHERE guild = ? and name = ?",
                    (guildid, memberid),
                ):
                    pass
                await db.commit()


class warnings:
    class Punishment:
        def __init__(self, punishment: str, duration: typing.Optional[int] = None):
            if (
                punishment.startswith("temp") or punishment == "timeout"
            ) and duration is None:
                raise Exception("duration cannot be None for temporary punishments.")
            if punishment not in [
                "temp_ban",
                "temp_mute",
                "mute",
                "ban",
                "kick",
                "timeout",
            ]:
                raise Exception("Invalid punishment.")
            self.punishment = punishment
            if not punishment.startswith("temp") and not punishment == "timeout":
                self.duration = None
            else:
                self.duration = duration

    @staticmethod
    async def warn(
        inter: ApplicationCommandInteraction,
        member: discord.Member,
        reason: typing.Optional[str] = None,
        expires: Optional[int] = -1,
    ) -> None:
        db = warnings_db
        if len(str(reason)) > 256:
            reason = reason[:253] + "..."
        reason_str = str(reason)
        guildid = str(inter.guild.id)
        user = member
        member = str(member.id)
        async with db.execute(
            """CREATE TABLE if NOT EXISTS warnings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id TEXT,
        guild TEXT,
        reason TEXT,
        expires INTEGER
        )"""
        ):
            pass
        await db.commit()
        async with db.execute(
            "INSERT INTO warnings (member_id,guild,reason,expires) VALUES (?,?,?,?)",
            (member, guildid, reason_str, expires),
        ):
            pass
        await db.commit()
        if reason is None:
            msg = f"Warned {user.display_name}."
        else:
            msg = f"Warned {user.display_name}. Reason: {reason}"
        await inter.send(msg, ephemeral=EPHEMERAL)

    @staticmethod
    async def warnings_list(guild: int, member_id: int) -> List[str]:
        db = warnings_db
        try:
            async with db.execute(
                "SELECT reason FROM warnings WHERE guild = ? and member_id = ?",
                (str(guild), str(member_id)),
            ) as cursor:
                warn_list = []
                async for entry in cursor:
                    warn_list.append(entry[0])
                return warn_list
        except:
            return []

    @staticmethod
    async def warnings(
        inter: ApplicationCommandInteraction, member: discord.Member, warn_num: int = 0
    ) -> None:
        guildid = str(inter.guild.id)
        user = member
        member = str(member.id)
        db = warnings_db
        try:
            async with db.execute(
                "SELECT reason FROM warnings WHERE guild = ? and member_id = ?",
                (guildid, member),
            ) as cursor:
                number = 0
                warn_list = []
                async for entry in cursor:
                    number += 1
                    warn_list.append(entry[0])
                if number > 0:
                    if warn_num == 0:
                        def func(array, start_num, page_info):
                            embed = disnake.Embed(title=f"{user.display_name}'s Warnings", color=COLOR)
                            for i, warning in enumerate(array):
                                embed.add_field(
                                    name=f"Warning #{i+start_num}",
                                    value=f"Reason: {warning}",
                                    inline=False,
                                )
                            embed.set_footer(
                                text=f"Page {page_info[0]}/{page_info[1]} | Total Warnings: {number}")
                            return embed
                        view = utils.ListScroller(5, warn_list, func, inter)
                        embed = func(warn_list[0:5], 1, (1, math.ceil(len(warn_list)/5)))
                        await view.start()
                        await inter.send(embed=embed,view=view, ephemeral=EPHEMERAL)
                    else:
                        embed = discord.Embed(
                            color=COLOR, title=f"{user.display_name}'s Warnings"
                        )
                        if warn_num > len(warn_list):
                            await inter.send(
                                f"{user.display_name} does not have that many.",
                                ephemeral=EPHEMERAL,
                            )
                            return
                        embed.add_field(
                            name=f"Warning #{number} ",
                            value=f"Reason: {warn_list[warn_num - 1]}",
                            inline=False,
                        )
                        embed.set_footer(text=f"Total Warnings: {number}")
                        await inter.send(embed=embed, ephemeral=EPHEMERAL)
                else:
                    await inter.send(
                        f"{user.display_name} has no warnings.", ephemeral=EPHEMERAL
                    )
        except sqlite3.OperationalError:
            await inter.send(
                f"{user.display_name} has no warnings.", ephemeral=EPHEMERAL
            )

    @staticmethod
    async def unwarn(
        inter: ApplicationCommandInteraction, member, number: typing.Union[int, str]
    ) -> bool:
        user = member
        guild = str(inter.guild.id)
        member = str(member.id)
        number = str(number)
        number = number.lower()
        db = warnings_db
        try:
            async with db.execute(
                "SELECT reason FROM warnings WHERE guild = ? and member_id = ?",
                (guild, member),
            ) as cursor:
                count = 0
                async for _ in cursor:
                    count += 1
        except:
            msg = f"{user.display_name} has no warnings."
            await inter.send(msg, ephemeral=EPHEMERAL)
            return False
        if count < 1:
            msg = f"{user.display_name} has no warnings."
            await inter.send(msg, ephemeral=EPHEMERAL)
            return False
        if number == "all":
            async with db.execute(
                "DELETE FROM warnings WHERE guild = ? and member_id = ?",
                (guild, member),
            ):
                pass
            await db.commit()
            msg = f"Cleared all warnings from {user.display_name}."
            await inter.send(msg, ephemeral=EPHEMERAL)
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
                        (guild, member),
                    ) as cursor:
                        async for entry in cursor:
                            id, pos = entry
                            pos = str(pos)
                            dict.update({pos: id})
                    for x in number_list:
                        async with db.execute(
                            "DELETE FROM warnings WHERE id = ?", (dict[str(x)],)
                        ):
                            pass
                    await db.commit()
                    number_list = list(map(str, number_list))
                    number_list = ", ".join(number_list)
                    await inter.send(
                        f"Cleared warnings {number_list} from {user.display_name}.",
                        ephemeral=EPHEMERAL,
                    )
                else:
                    number = int(number)
                    dict = {}
                    async with db.execute(
                        "SELECT id,row_number() OVER (ORDER BY id) FROM warnings WHERE guild = ? and member_id = ?",
                        (guild, member),
                    ) as cursor:
                        async for entry in cursor:
                            id, pos = entry
                            pos = str(pos)
                            dict.update({pos: id})
                    async with db.execute(
                        "DELETE FROM warnings WHERE id = ?", (dict[str(number)],)
                    ):
                        pass
                    await db.commit()
                    msg = f"Cleared {user.display_name}'s #{number} warning."
                    await inter.send(msg, ephemeral=EPHEMERAL)
                    return True
            except:
                if number == "all":
                    msg = f"{user.display_name} has no warnings."
                else:
                    msg = f"{user.display_name} does not have that many warnings."
                await inter.send(msg, ephemeral=EPHEMERAL)
                return False

    @staticmethod
    async def punish(
        inter: ApplicationCommandInteraction,
        member: discord.Member,
        punishments: typing.Mapping[int, Punishment],
        add_role: typing.Optional[int] = None,
        remove_role: typing.Optional[int] = None,
        before: Optional[
            Callable[
                [int, Punishment, discord.Member], Awaitable[Optional[discord.Message]]
            ]
        ] = None,
    ) -> None:
        memberid = str(member.id)
        guild = str(inter.guild.id)
        db = warnings_db
        async with db.execute(
            """CREATE TABLE IF NOT EXISTS tempmute(
                    guild TEXT,
                    member TEXT,
                    time DATETIME
                    )"""
        ):
            pass
        async with db.execute(
            """CREATE TABLE IF NOT EXISTS tempban(
                    guild TEXT,
                    member TEXT,
                    time DATETIME
                    )"""
        ):
            pass
        await db.commit()
        try:
            async with db.execute(
                "SELECT reason FROM warnings WHERE guild = ? and member_id = ?",
                (guild, memberid),
            ) as cursor:
                warnings_number = 0
                async for _ in cursor:
                    warnings_number += 1
        except:
            return
        if warnings_number not in punishments:
            return
        if punishments[warnings_number].duration is not None:
            if punishments[warnings_number].punishment == "temp_ban":
                msg = await before(
                    warnings_number, punishments[warnings_number], member
                )
                time = punishments[warnings_number].duration
                try:
                    await member.ban(
                        reason=f"You have received {warnings_number} warning(s)."
                    )
                except (discord.Forbidden, discord.HTTPException) as e:
                    with contextlib.suppress(Exception):
                        await msg.delete()
                    raise e
                time = datetime.datetime.now() + datetime.timedelta(seconds=time)
                async with db.execute(
                    "INSERT INTO tempban (guild,member,time) VALUES (?,?,?)",
                    (guild, memberid, time),
                ):
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
                        with contextlib.suppress(
                            discord.Forbidden, discord.HTTPException
                        ):
                            await member.remove_roles(remove_role)
                    await member.edit(
                        reason=f"You have received {warnings_number} warning(s).",
                        voice_channel=None,
                    )
                    await mute_on_join.mute_add(inter.guild, member)
                    time = datetime.datetime.now() + datetime.timedelta(seconds=time)
                    async with db.execute(
                        "INSERT INTO tempmute (guild,member,time) VALUES (?,?,?)",
                        (guild, memberid, time),
                    ):
                        pass
                    await db.commit()
                    await before(warnings_number, punishments[warnings_number], member)
            else:
                time = punishments[warnings_number].duration
                await member.timeout(
                    reason=f"You have received {warnings_number} warning(s).",
                    duration=time,
                )
                await before(warnings_number, punishments[warnings_number], member)
                return
        else:
            if punishments[warnings_number].punishment == "ban":
                msg = await before(
                    warnings_number, punishments[warnings_number], member
                )
                try:
                    await member.ban(
                        reason=f"You have received {warnings_number} warning(s)."
                    )
                except (discord.Forbidden, discord.HTTPException) as e:
                    with contextlib.suppress(Exception):
                        await msg.delete()
                    raise e
                return
            if punishments[warnings_number].punishment == "kick":
                msg = await before(
                    warnings_number, punishments[warnings_number], member
                )
                try:
                    await member.kick(
                        reason=f"You have received {warnings_number} warning(s)."
                    )
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
                    with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                        await member.remove_roles(remove_role)
                if add_role is not None:
                    await member.add_roles(add_role)
                await member.edit(
                    reason=f"You have received {warnings_number} warning(s).",
                    voice_channel=None,
                )
                await mute_on_join.mute_add(inter.guild, member)
                await before(warnings_number, punishments[warnings_number], member)

    @staticmethod
    async def temp_mute_loop(
        bot: commands.Bot,
        add_role_func: Callable[[int], Awaitable[Optional[int]]],
        remove_role_func: Optional[Callable[[int], Awaitable[Optional[int]]]] = None,
    ) -> None:
        try:
            db = warnings_db
        except NameError:
            return
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT guild,member,time FROM tempmute") as cursor:
                async for entry in cursor:
                    guild_id, member_id, time_str = entry
                    guild = bot.get_guild(int(guild_id))
                    if not isinstance(guild, discord.Guild):
                        async with db.execute(
                            "DELETE FROM tempmute WHERE guild = ?", (str(guild_id),)
                        ):
                            pass
                        continue
                    member = guild.get_member(int(member_id))
                    if not isinstance(member, discord.Member):
                        async with db.execute(
                            "DELETE FROM tempmute WHERE guild = ? and member = ?",
                            (str(guild_id), str(member_id)),
                        ):
                            pass
                        continue
                    time = datetime.datetime.fromisoformat(time_str)
                    role_add = await add_role_func(int(guild_id))
                    if remove_role_func is None:
                        role_remove = None
                    else:
                        role_remove = await remove_role_func(int(guild_id))
                    if datetime.datetime.now() >= time:
                        with contextlib.suppress(
                            discord.Forbidden, discord.HTTPException
                        ):
                            await member.add_roles(guild.get_role(int(role_remove)))
                        with contextlib.suppress(
                            discord.Forbidden, discord.HTTPException
                        ):
                            await member.remove_roles(guild.get_role(int(role_add)))
                        with contextlib.suppress(sqlite3.Error):
                            async with db.execute(
                                "DELETE FROM tempmute WHERE guild = ? and member = ? and time = ?",
                                (str(guild.id), str(member.id), time_str),
                            ):
                                pass
                        await mute_on_join.mute_remove(guild, member)
            await db.commit()

    @staticmethod
    async def temp_ban_loop(bot: commands.Bot) -> None:
        try:
            db = warnings_db
        except NameError:
            return
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT guild,member,time FROM tempban") as cursor:
                async for entry in cursor:
                    guild_id, member, time_str = entry
                    guild = bot.get_guild(int(guild_id))
                    if not isinstance(guild, discord.Guild):
                        async with db.execute(
                            "DELETE FROM tempban WHERE guild = ?", (str(guild_id),)
                        ):
                            pass
                        continue
                    time = datetime.datetime.fromisoformat(time_str)
                    if datetime.datetime.now() >= time:
                        async with db.execute(
                            "DELETE FROM tempban WHERE guild = ? and member = ? and time = ?",
                            (str(guild.id), member.display_name, time_str),
                        ):
                            pass
                        with contextlib.suppress(
                            discord.Forbidden, discord.HTTPException
                        ):
                            await guild.unban(discord.Object(id=int(member)))
                await db.commit()

    @staticmethod
    async def expire_loop() -> None:
        try:
            db = warnings_db
        except NameError:
            return
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
    async def command(
        inter: ApplicationCommandInteraction,
        emoji: str,
        role: str,
        title: str,
        description: str,
    ) -> None:
        db = rr_db
        await inter.send(
            "Attempting to create reaction role...", ephemeral=EPHEMERAL
        )
        async with db.execute(
            """CREATE TABLE IF NOT EXISTS rr(
        msg_id TEXT,
        emoji UNICODE,
        role TEXT,
        guild TEXT,
        channel TEXT
        )"""
        ):
            pass
        await db.commit()
        embed = discord.Embed(title=title, color=COLOR, description=description)
        role = role.replace("<", "")
        role = role.replace(">", "")
        role = role.replace("@", "")
        role = role.replace("&", "")
        emoji = emoji.replace(" ", "")
        emoji_list = emoji.split(",")
        try:
            role_list = [inter.guild.get_role(int(r)) for r in role.split(",")]
        except:
            await inter.followup.send("Invalid role", ephemeral=EPHEMERAL)
            return
        if len(role_list) != len(emoji_list):
            await inter.followup.send(
                "Emoji list must be same length as role list.", ephemeral=EPHEMERAL
            )
            return
        if len(emoji_list) > 1:
            for role in role_list:
               if role is None:
                await inter.followup.send("Invalid roles", ephemeral=EPHEMERAL)
                return
            msg = await inter.channel.send(embed=embed)
            for i, e in enumerate(emoji_list):
                role = role_list[i]
                try:
                    await msg.add_reaction(e)
                except (discord.HTTPException):
                    await inter.followup.send("Invalid emojis", ephemeral=EPHEMERAL)
                    await msg.delete()
                    return
                async with db.execute(
                    "INSERT INTO rr (msg_id,emoji,role,guild,channel) VALUES (?,?,?,?,?)",
                    (
                        str(msg.id),
                        e,
                        str(role.id),
                        str(inter.guild.id),
                        str(inter.channel.id),
                    ),
                ):
                    pass
            await inter.followup.send(
                "Successfully created the reaction role.", ephemeral=EPHEMERAL
            )
            await db.commit()
        else:
            role = role_list[0]
            if role is None:
                await inter.followup.send("Invalid role", ephemeral=EPHEMERAL)
                return
            msg = await inter.channel.send(embed=embed)
            try:
                await msg.add_reaction(emoji)
            except (discord.HTTPException):
                await inter.followup.send("Invalid emojis", ephemeral=EPHEMERAL)
                await msg.delete()
                return
            async with db.execute(
                "INSERT INTO rr (msg_id,emoji,role,guild,channel) VALUES (?,?,?,?,?)",
                (
                    str(msg.id),
                    emoji,
                    str(role.id),
                    str(inter.guild.id),
                    str(inter.channel.id),
                ),
            ):
                pass
            await db.commit()
            await inter.followup.send(
                "Successfully created the reaction role.", ephemeral=EPHEMERAL
            )

    @staticmethod
    async def add(payload: discord.RawReactionActionEvent, bot: commands.Bot) -> None:
        if payload.guild_id is None:
            return
        if payload.member.bot:
            return
        db = rr_db
        guild = bot.get_guild(payload.guild_id)
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT emoji,role FROM rr WHERE guild = ? and msg_id = ?",
                (str(guild.id), str(payload.message_id)),
            ) as cursor:
                async for entry in cursor:
                    emoji, role = entry
                    role = guild.get_role(int(role))
                    if str(payload.emoji) == emoji:
                        with contextlib.suppress(
                            discord.Forbidden, discord.HTTPException
                        ):
                            await payload.member.add_roles(role)

    @staticmethod
    async def remove(
        payload: discord.RawReactionActionEvent, bot: commands.Bot
    ) -> None:
        if payload.guild_id is None:
            return
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member.bot:
            return
        db = rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT emoji,role FROM rr WHERE guild = ? and msg_id = ?",
                (str(guild.id), str(payload.message_id)),
            ) as cursor:
                async for entry in cursor:
                    emoji, role = entry
                    role = guild.get_role(int(role))
                    if str(payload.emoji) == emoji:
                        with contextlib.suppress(
                            discord.Forbidden, discord.HTTPException
                        ):
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
        await inter.send(msg, ephemeral=EPHEMERAL)

    @staticmethod
    async def clear_one(inter: ApplicationCommandInteraction, message_id: int) -> None:
        guild = str(inter.guild.id)
        message_id = str(message_id)
        db = rr_db
        message_id = message_id.replace(" ", "")
        message_id = message_id.split(",")
        for x in message_id:
            try:
                async with db.execute(
                    "DELETE FROM rr WHERE guild = ? and msg_id = ?", (guild, x)
                ):
                    pass
            except:
                break
        await db.commit()
        message_id = ", ".join(message_id)
        msg = f"Deleted all reaction role info with message ID(s): {message_id}"
        await inter.send(msg, ephemeral=EPHEMERAL)

    @staticmethod
    async def clear_on_message_delete(message: discord.Message) -> None:
        if message.guild is None:
            return
        db = rr_db
        guild = str(message.guild.id)
        id = str(message.id)
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT msg_id FROM rr WHERE guild = ?", (guild,)
            ) as cursor:
                async for entry in cursor:
                    msg_id = entry[0]
                    if msg_id == id:
                        async with db.execute(
                            "DELETE FROM rr WHERE msg_id = ? and guild = ?",
                            (id, guild),
                        ):
                            pass
                        break
                await db.commit()

    @staticmethod
    async def clear_on_channel_delete(channel: discord.TextChannel) -> None:
        channel_id = channel.id
        guild = channel.guild.id
        db = rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT channel FROM rr WHERE guild = ?", (str(guild),)
            ) as cursor:
                async for entry in cursor:
                    channel = int(entry[0])
                    if channel == channel_id:
                        async with db.execute(
                            "DELETE FROM rr WHERE guild = ? and channel = ?",
                            (str(guild), str(channel)),
                        ):
                            pass
                        break
                await db.commit()

    @staticmethod
    async def clear_on_thread_delete(thread: discord.Thread) -> None:
        thread_id = thread.id
        guild = thread.guild.id
        db = rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT channel FROM rr WHERE guild = ?", (str(guild),)
            ) as cursor:
                async for entry in cursor:
                    channel = int(entry[0])
                    if channel == thread_id:
                        async with db.execute(
                            "DELETE FROM rr WHERE guild = ? and channel = ?",
                            (str(guild), str(channel)),
                        ):
                            pass
                        break
                await db.commit()

    @staticmethod
    async def clear_on_bulk_message_delete(
        payload: discord.RawBulkMessageDeleteEvent,
    ) -> None:
        ids = payload.message_ids
        guild = payload.guild_id
        if guild is None:
            return
        db = rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT msg_id FROM rr WHERE guild = ?", (str(guild),)
            ) as cursor:
                async for entry in cursor:
                    msg_id = int(entry[0])
                    for id in ids:
                        if id == msg_id:
                            async with db.execute(
                                "DELETE FROM rr WHERE guild = ? and msg_id = ?",
                                (str(guild), str(msg_id)),
                            ):
                                pass
                        break
                    break
            await db.commit()

    class Delete(disnake.ui.Button):
        async def callback(self, inter: discord.MessageInteraction) -> None:
            if self.view.delete_lock.locked():
                return
            async with self.view.delete_lock:
                msg_id = self.view.list[self.view.pos * self.view.count:self.view.pos * self.view.count + self.view.count][0][2]
                channel = self.view.list[self.view.pos * self.view.count:self.view.pos * self.view.count + self.view.count][0][3]
                self.view.list.pop(self.view.pos)
                await self.view.reset()
                try:
                    async with rr_db.execute(
                            "DELETE FROM rr WHERE guild = ? and msg_id = ?", (str(inter.guild.id), str(msg_id))
                    ):
                        pass
                except:
                    pass
                with contextlib.suppress(Exception):
                    msg = await channel.fetch_message(msg_id)
                    await msg.delete()
                await rr_db.commit()
                if len(self.view.list) == 0:
                    self.view.clear_items()
                    self.view.stop()
                    await inter.response.edit_message("There are no reaction roles in this server.", view=self.view, embed=None)
                    self.view.clear_data()
                    return
                await self.view.reset()
                self.view.add_item(self)
                embed = self.view.func(
                    self.view.list[self.view.pos * self.view.count:self.view.pos * self.view.count + self.view.count],
                    self.view.pos * self.view.count + 1, (self.view.pos + 1, self.view.pages))
                await inter.response.edit_message(embed=embed, view=self.view)

    @staticmethod
    async def display(inter: ApplicationCommandInteraction) -> None:
        guild = str(inter.guild.id)
        db = rr_db
        reaction_roles = []
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT msg_id FROM rr WHERE guild = ? GROUP BY msg_id", (guild,)
            ) as cursor:
                number = 0
                async for entry in cursor:
                    async with db.execute(
                        "SELECT role,emoji,channel,msg_id FROM rr WHERE guild = ? and msg_id = ?",
                        (guild, entry[0]),
                    ) as f:
                        roles = []
                        emojis = []
                        channel = None
                        msg_id = int(entry[0])
                        async for entry in f:
                            role, emoji, channel, msg_id = entry
                            role = inter.guild.get_role(int(role))
                            roles.append(role)
                            emojis.append(emoji)
                            channel = channel
                        channel = inter.guild.get_channel(int(channel))
                        reaction_roles.append((roles, emojis, msg_id, channel))
            if len(reaction_roles) > 0:
                def func(array, start_num, page_info):
                    embed = disnake.Embed(title=f"Reaction Roles", color=COLOR)
                    embed.add_field(name=f"Roles", value=" ".join([f"{role.mention if role is not None else '@deleted-role'}" for role in array[0][0]]), inline=False)
                    embed.add_field(name=f"Emojis", value=" ".join(array[0][1]), inline=False)
                    embed.add_field(name=f"Channel", value=f"{array[0][3].mention if array[0][3] is not None else '#deleted-channel'}", inline=False)
                    embed.add_field(name=f"Message ID", value=array[0][2], inline=False)
                    embed.set_footer(
                        text=f"Page {page_info[0]}/{page_info[1]}")
                    return embed
                view = utils.ListScroller(1, reaction_roles, func, inter)
                embed = func(reaction_roles[0:1], 1, (1, len(reaction_roles)))
                delete_button = rr.Delete(label="Delete", style=disnake.ButtonStyle.red, custom_id="delete")
                view.delete_lock = asyncio.Semaphore(1)
                await view.start()
                view.add_item(delete_button)
                await inter.send(embed=embed, view=view, ephemeral=EPHEMERAL)
                return
        await inter.send("There are no reaction roles in this server.", ephemeral=EPHEMERAL)