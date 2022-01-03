# This library is in development and bugs can be expected. If you encounter any bugs, want to give feedback, or would like to contribute, join our Discord server.
# https://discord.gg/TUUbzTa3B7

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

import os
import typing
import disnake as discord
import datetime
import aiosqlite
import asyncio
from disnake.ext import commands
from disnake import MessageCommandInteraction
from dpys import utils

RED = 0xD40C00
BLUE = 0x0000FF
GREEN = 0x32C12C
version = "5.2.5"
EPHEMERAL = True

print("We recommend that you read https://jgltechnologies.com/dpys before you use DPYS.")


class misc:

    @staticmethod
    async def reload(inter: MessageCommandInteraction, bot: commands.Bot, cogs: typing.List[str]) -> None:
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
    async def clear_data_on_guild_remove(guild: discord.Guild, dir: str) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        async with aiosqlite.connect("warnings.db") as db:
            try:
                await db.execute("DELETE FROM tempmute WHERE guild = ?", (str(guild.id),))
            except:
                pass

            try:
                await db.execute("DELETE FROM tempban WHERE guild = ?", (str(guild.id),))
            except:
                pass

            try:
                await db.execute("DELETE FROM warnings WHERE guild = ?", (str(guild.id),))
            except:
                pass
            await db.commit()
        async with aiosqlite.connect("rr.db") as db:
            try:
                await db.execute("DELETE FROM rr WHERE guild = ?", (str(guild.id),))
            except:
                pass
            await db.commit()
        async with aiosqlite.connect("muted.db") as db:
            try:
                await db.execute("DELETE FROM muted WHERE guild = ?", (str(guild.id),))
            except:
                pass
            await db.commit()
        async with aiosqlite.connect("curse.db") as db:
            try:
                await db.execute("DELETE FROM curses WHERE guild = ?", (str(guild.id),))
            except:
                pass
            await db.commit()


class admin:

    @staticmethod
    async def mute(inter: MessageCommandInteraction, member: discord.Member, role_add: int,
                   role_remove: typing.Optional[int] = None, reason: str = None) -> None:
        if inter.guild.get_role(role_add) in member.roles:
            await inter.response.send_message(f"{member.name}#{member.discriminator} is already muted.",
                                              ephemeral=EPHEMERAL)
            return
        if len(str(reason)) > 256:
            reason = reason[:256]
        else:
            if not isinstance(inter.guild.get_role(role_add), discord.Role):
                return
            await member.add_roles(inter.guild.get_role(role_add))
            if role_remove is not None:
                try:
                    await member.remove_roles(inter.guild.get_role(role_remove))
                except:
                    pass
            if reason is None:
                await inter.response.send_message(f"Muted {str(member)}.", ephemeral=EPHEMERAL)
            else:
                await inter.response.send_message(f"Muted {member.name}#{member.discriminator}. Reason: {reason}",
                                                  ephemeral=EPHEMERAL)

    @staticmethod
    async def unmute(inter: MessageCommandInteraction, member: discord.Member, role_remove: int,
                     role_add: typing.Optional[int] = None) -> None:
        if inter.guild.get_role(role_remove) not in member.roles:
            await inter.response.send_message(f"{member.name}#{member.discriminator} is not muted.",
                                              ephemeral=EPHEMERAL)
            return
        else:
            if not isinstance(inter.guild.get_role(role_remove), discord.Role):
                return
            await member.remove_roles(inter.guild.get_role(role_remove))
            if role_add is not None:
                try:
                    await member.add_roles(inter.guild.get_role(role_add))
                except:
                    pass
            await inter.response.send_message(f"Unmuted {member.name}#{member.discriminator}.", ephemeral=EPHEMERAL)

    @staticmethod
    async def clear(inter: MessageCommandInteraction, amount: typing.Optional[int] = 99999999999999999) -> int:
        limit = datetime.datetime.now() - datetime.timedelta(weeks=2)
        purged = await inter.channel.purge(limit=amount, after=limit)
        purged = len(purged)
        if purged != 1:
            message = f"Cleared {purged} messages."
        else:
            message = f"Cleared {purged} message."
        await inter.response.send_message(message, ephemeral=EPHEMERAL)
        return purged

    @staticmethod
    async def kick(inter: MessageCommandInteraction, member: discord.Member,
                   reason: typing.Optional[str] = None) -> None:
        if len(str(reason)) > 256:
            reason = reason[:256]
        await member.kick(reason=reason)
        if reason is None:
            message = f"Kicked {member.name}#{member.discriminator}."
        else:
            message = f"Kicked {member.name}#{member.discriminator}. Reason: {reason}"
        await inter.response.send_message(message, ephemeral=EPHEMERAL)

    @staticmethod
    async def ban(inter: MessageCommandInteraction, member: discord.Member,
                  reason: typing.Optional[str] = None) -> None:
        if len(str(reason)) > 256:
            reason = reason[:256]
        await member.ban(reason=reason)
        if reason is None:
            message = f"Banned {member.name}#{member.discriminator}."
        else:
            message = f"Banned {member.name}#{member.discriminator}. Reason: {reason}"
        await inter.response.send_message(message, ephemeral=EPHEMERAL)

    @staticmethod
    async def softban(inter: MessageCommandInteraction, member: discord.Member,
                      reason: typing.Optional[str] = None) -> None:
        if len(str(reason)) > 256:
            reason = reason[:256]
        await member.ban(reason=reason)
        if reason is None:
            message = f"Soft banned {member.name}#{member.discriminator}."
        else:
            message = f"Soft banned {member.name}#{member.discriminator}. Reason: {reason}"
        await inter.response.send_message(message, ephemeral=EPHEMERAL)
        await member.unban()

    @staticmethod
    async def unban(inter: MessageCommandInteraction, member: typing.Union[str, int]) -> None:
        bans = await inter.guild.bans()
        if isinstance(member, int):
            ban = [ban for ban in bans if ban.user.id == member]
        else:
            try:
                name, discrim = member.split("#")
            except ValueError:
                raise commands.errors.UserNotFound(member)
            ban = [ban for ban in bans if ban.user.discriminator ==
                   discrim and ban.user.name == name]
        if not ban:
            await inter.response.send_message(f"{member} is not banned.", ephemeral=EPHEMERAL)
            return
        await inter.guild.unban(ban[0].user)
        await inter.response.send_message(f"Unbanned {member}.", ephemeral=EPHEMERAL)


class curse:

    @staticmethod
    async def add_banned_word(inter: MessageCommandInteraction, word: str, dir: str) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        word = word.lower()
        guildid = str(inter.guild.id)
        async with aiosqlite.connect("curse.db") as db:
            await db.execute(f"""CREATE TABLE if NOT EXISTS curses(
            curse TEXT,
            guild TEXT,
            PRIMARY KEY (curse,guild)
            )""")
            await db.commit()
            words = word.replace(" ", "")
            words = words.split(",")
            words = set(words)
            curses = await utils.GuildData.curse_set(inter.guild.id, dir)
            for x in words:
                if x in curses:
                    msg = f"{x} is already in the list."
                    await inter.response.send_message(msg, ephemeral=EPHEMERAL)
                    return
                await db.execute("INSERT INTO curses (curse,guild) VALUES (?,?)", (x, guildid))
            await db.commit()
            await inter.response.send_message("The word(s) have been added to the list.", ephemeral=EPHEMERAL)

    @staticmethod
    async def remove_banned_word(inter: MessageCommandInteraction, word: str, dir: str) -> None:
        async with aiosqlite.connect("curse.db") as db:
            await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
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
                        msg = "None of those words are in the list."
                    else:
                        msg = "That word is not in the list."
                    await inter.response.send_message(msg, ephemeral=EPHEMERAL)
                    return
                for x in word:
                    await db.execute("DELETE FROM curses WHERE curse = ? and guild = ?", (x, guildid))
                    await db.commit()
                await inter.response.send_message("The word(s) have been removed.", ephemeral=EPHEMERAL)
            except:
                await inter.response.send_message("A list has not been created yet.", ephemeral=EPHEMERAL)

    @staticmethod
    async def message_filter(message: discord.Message, dir: str,
                             exempt_roles: typing.Optional[typing.List[int]] = None) -> None:
        if message.author.bot or message.guild is None:
            return
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guildid = str(message.guild.id)
        if exempt_roles is not None:
            for id in exempt_roles:
                role = message.guild.get_role(id)
                if role in message.author.roles or message.author.top_role.position > role.position or message.author.bot:
                    return
            else:
                try:
                    messagecontent = message.content.lower()
                    async with aiosqlite.connect("curse.db") as db:
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
                async with aiosqlite.connect("curse.db") as db:
                    async with db.execute("SELECT curse FROM curses WHERE guild = ?", (guildid,)) as cursor:
                        async for entry in cursor:
                            if entry[0] in messagecontent.split():
                                await message.delete()
                                await message.channel.send("Do not say that here!", delete_after=5)
            except:
                return

    @staticmethod
    async def message_edit_filter(after: discord.Message, dir: str,
                                  exempt_roles: typing.Optional[typing.List[int]] = None) -> None:
        message = after
        if message.author.bot or message.guild is None:
            return
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
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
                        async with aiosqlite.connect("curse.db") as db:
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
                    async with aiosqlite.connect("curse.db") as db:
                        async with db.execute("SELECT curse FROM curses WHERE guild = ?", (guildid,)) as cursor:
                            async for entry in cursor:
                                if entry[0] in messagecontent.split():
                                    await message.delete()
                                    await message.channel.send("Do not say that here!", delete_after=5)
                except:
                    return

    @staticmethod
    async def clear_words(inter: MessageCommandInteraction, dir: str) -> None:
        guildid = str(inter.guild.id)
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        try:
            async with aiosqlite.connect("curse.db") as db:
                await db.execute("DELETE FROM curses WHERE guild = ?", (guildid,))
                await db.commit()
                await inter.response.send_message("Cleared all curses from this server", ephemeral=EPHEMERAL)
        except:
            msg = "There is not a curse list for this server."
            await inter.response.send_message(msg, ephemeral=EPHEMERAL)


class mute_on_join:

    @staticmethod
    async def mute_add(guild: discord.Guild, member: discord.Member, dir: str) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guildid = str(guild.id)
        member = str(member.id)
        try:
            async with aiosqlite.connect("muted.db") as db:
                await db.execute(f"""CREATE TABLE if NOT EXISTS muted(
                name TEXT,
                guild TEXT,
                PRIMARY KEY (name,guild)
                )""")
                await db.commit()
                await db.execute("INSERT INTO muted (name,guild) VALUES (?,?)", (member, guildid))
                await db.commit()
        except:
            pass

    @staticmethod
    async def mute_remove(guild: discord.Guild, member: discord.Member, dir: str) -> None:
        member = str(member.id)
        guildid = str(guild.id)
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        try:
            async with aiosqlite.connect("muted.db") as db:
                await db.execute("DELETE FROM muted WHERE name = ? and guild = ?", (member, guildid))
                await db.commit()
        except:
            pass

    @staticmethod
    async def mute_on_join(member: discord.Member, role: int, dir: str) -> None:
        user = member
        guildid = str(member.guild.id)
        muted_role = member.guild.get_role(role)
        if not isinstance(muted_role, discord.Role):
            return
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        member = str(member.id)
        try:
            async with aiosqlite.connect("muted.db") as db:
                async with db.execute("SELECT name FROM muted WHERE guild = ?", (guildid,)) as cursor:
                    async for entry in cursor:
                        if entry[0] == member:
                            await user.add_roles(muted_role)
        except:
            pass

    @staticmethod
    async def manual_unmute_check(after: discord.Member, roleid: int, dir: str) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        if after.bot:
            return
        guildid = str(after.guild.id)
        role = after.guild.get_role(roleid)
        async with aiosqlite.connect("muted.db") as db:
            memberid = str(after.id)
            try:
                if role not in after.roles:
                    await db.execute("DELETE FROM muted WHERE guild = ? and name = ?", (guildid, memberid))
                    await db.commit()
            except:
                pass


class warnings:
    class Punishment:
        def __init__(self, punishment: str, duration: typing.Optional[int] = None):
            if punishment.startswith("temp") and duration is None:
                raise Exception("duration cannot be None for temporary punishments.")
            if punishment not in ["temp_ban", "temp_mute", "mute", "ban", "kick"]:
                raise Exception("Invalid punishment.")
            self.punishment = punishment
            if not punishment.startswith("temp"):
                self.duration = None
            else:
                self.duration = duration

    @staticmethod
    async def warn(inter: MessageCommandInteraction, member: discord.Member, dir: str,
                   reason: typing.Optional[str] = None) -> None:
        if len(str(reason)) > 256:
            reason = reason[:256]
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        reason_str = str(reason)
        guildid = str(inter.guild.id)
        user = member
        member = str(member.id)
        async with aiosqlite.connect("warnings.db") as db:
            await db.execute("""CREATE TABLE if NOT EXISTS warnings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id TEXT,
            guild TEXT,
            reason TEXT
            )""")
            await db.commit()
            await db.execute("INSERT INTO warnings (member_id,guild,reason) VALUES (?,?,?)",
                             (member, guildid, reason_str))
            await db.commit()
            if reason is None:
                msg = f"Warned {user.name}#{user.discriminator}."
            else:
                msg = f"Warned {user.name}#{user.discriminator}. Reason: {reason}"
            await inter.response.send_message(msg, ephemeral=EPHEMERAL)

    @staticmethod
    async def warnings_list(inter: MessageCommandInteraction, member: discord.Member, dir: str) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guildid = str(inter.guild.id)
        user = member
        member = str(member.id)
        try:
            async with aiosqlite.connect("warnings.db") as db:
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
    async def unwarn(inter: MessageCommandInteraction, member, dir, number: typing.Union[int, str]) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        user = member
        guild = str(inter.guild.id)
        member = str(member.id)
        number = str(number)
        number = number.lower()
        async with aiosqlite.connect("warnings.db") as db:
            try:
                async with db.execute("SELECT reason FROM warnings WHERE guild = ? and member_id = ?",
                                      (guild, member)) as cursor:
                    count = 0
                    async for entry in cursor:
                        count += 1
            except:
                msg = f"{user.name}#{user.discriminator} has no warnings."
                await inter.response.send_message(msg, ephemeral=EPHEMERAL)
                return
            if count < 1:
                msg = f"{user.name}#{user.discriminator} has no warnings."
                await inter.response.send_message(msg, ephemeral=EPHEMERAL)
                return
            if number == "all":
                await db.execute("DELETE FROM warnings WHERE guild = ? and member_id = ?", (guild, member))
                await db.commit()
                msg = f"Cleared all warnings from {user.name}#{user.discriminator}."
                await inter.response.send_message(msg, ephemeral=EPHEMERAL)
                return
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
                            await db.execute("DELETE FROM warnings WHERE id = ?", (dict[str(x)],))
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
                        await db.execute("DELETE FROM warnings WHERE id = ?", (dict[str(number)],))
                        await db.commit()
                        msg = f"Cleared {user.name}#{user.discriminator}'s #{number} warning."
                        await inter.response.send_message(msg, ephemeral=EPHEMERAL)
                except:
                    if number == "all":
                        msg = f"{user.name}#{user.discriminator} has no warnings."
                    else:
                        msg = f"{user.name}#{user.discriminator} does not have that many warnings."
                    await inter.response.send_message(msg, ephemeral=EPHEMERAL)

    @staticmethod
    async def punish(inter: MessageCommandInteraction, member: discord.Member, dir: str,
                     punishments: typing.List[typing.Optional[Punishment]],
                     add_role: typing.Optional[int] = None, remove_role: typing.Optional[int] = None) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        memberid = str(member.id)
        guild = str(inter.guild.id)
        async with aiosqlite.connect("warnings.db") as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS tempmute(
                        guild TEXT,
                        member TEXT,
                        time DATETIME
                        )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS tempban(
                        guild TEXT,
                        member TEXT,
                        time DATETIME
                        )""")
            await db.commit()
            try:
                async with db.execute("SELECT reason FROM warnings WHERE guild = ? and member_id = ?",
                                      (guild, memberid)) as cursor:
                    warnings_number = 0
                    async for _ in cursor:
                        warnings_number += 1
            except:
                return

            try:
                if punishments[warnings_number - 1] is None:
                    return
            except:
                return
            if punishments[warnings_number - 1].duration is not None:
                if punishments[warnings_number - 1].punishment == "temp_ban":
                    time = punishments[warnings_number - 1].duration
                    await member.ban(reason=f"You have received {warnings_number} warnings.")
                    time = datetime.datetime.now() + datetime.timedelta(seconds=time)
                    await db.execute("INSERT INTO tempban (guild,member,time) VALUES (?,?,?)",
                                     (guild, memberid, time))
                    await db.commit()
                    return
                else:
                    add_role = inter.guild.get_role(add_role)
                    if not isinstance(add_role, discord.Role):
                        return
                    remove_role = inter.guild.get_role(remove_role)
                    if add_role in member.roles:
                        return
                    else:
                        time = punishments[warnings_number - 1].duration
                        try:
                            await member.add_roles(add_role)
                        except:
                            pass
                        if remove_role is not None:
                            try:
                                await member.remove_roles(remove_role)
                            except:
                                pass
                        await mute_on_join.mute_add(inter.guild, member, dir)
                        time = datetime.datetime.now() + datetime.timedelta(seconds=time)
                        await db.execute("INSERT INTO tempmute (guild,member,time) VALUES (?,?,?)",
                                         (guild, memberid, time))
                        await db.commit()
                        return
            else:
                if punishments[warnings_number - 1].punishment == "ban":
                    await member.ban(reason=f"You have received {warnings_number} warnings.")
                    return
                if punishments[warnings_number - 1].punishment == "kick":
                    await member.kick(reason=f"You have received {warnings_number} warnings.")
                    return
                if punishments[warnings_number - 1].punishment == "mute":
                    add_role = inter.guild.get_role(add_role)
                    remove_role = inter.guild.get_role(remove_role)
                    if not isinstance(add_role, discord.Role):
                        return
                    if remove_role is not None:
                        try:
                            await member.remove_roles(remove_role)
                        except:
                            pass
                    if add_role is not None:
                        try:
                            await member.add_roles(add_role)
                        except:
                            pass
                    await mute_on_join.mute_add(inter.guild, member, dir)

    @staticmethod
    async def temp_mute_loop(dir: str, bot: commands.Bot, add_role_func: typing.Awaitable,
                             remove_role_func: typing.Optional[typing.Awaitable] = None) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        async with aiosqlite.connect("warnings.db") as db:
            try:
                async with db.execute("SELECT guild,member,time FROM tempmute") as cursor:
                    async for entry in cursor:
                        guild_id, member_id, time_str = entry
                        try:
                            guild = bot.get_guild(int(guild_id))
                            if not isinstance(guild, discord.Guild):
                                await db.execute("DELETE FROM tempmute WHERE guild = ?", (str(guild_id),))
                                await db.commit()
                                continue
                            member = guild.get_member(int(member_id))
                            if not isinstance(member, discord.Member):
                                await db.execute("DELETE FROM tempmute WHERE guild = ? and member = ?",
                                                 (str(guild_id), str(member_id)))
                                await db.commit()
                                continue
                            time = datetime.datetime.fromisoformat(time_str)
                            role_add = await add_role_func(int(guild_id))
                            if remove_role_func is None:
                                role_remove = None
                            else:
                                role_remove = await remove_role_func(int(guild_id))
                            if datetime.datetime.now() >= time:
                                if role_add is not None:
                                    try:
                                        await member.add_roles(guild.get_role(int(role_remove)))
                                    except:
                                        pass
                                    try:
                                        await member.remove_roles(guild.get_role(int(role_add)))
                                    except:
                                        pass
                                await db.execute("DELETE FROM tempmute WHERE guild = ? and member = ? and time = ?",
                                                 (str(guild.id), str(member.id), time_str))
                                await db.commit()
                                await mute_on_join.mute_remove(guild, member, dir)
                        except:
                            continue
            except:
                pass

    @staticmethod
    async def temp_ban_loop(dir: str, bot: commands.Bot) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        async with aiosqlite.connect("warnings.db") as db:
            try:
                async with db.execute("SELECT guild,member,time FROM tempban") as cursor:
                    async for entry in cursor:
                        guild_id, member, time_str = entry
                        try:
                            guild = bot.get_guild(int(guild_id))
                            if not isinstance(guild, discord.Guild):
                                await db.execute("DELETE FROM tempban WHERE guild = ?", (str(guild_id),))
                                await db.commit()
                                continue
                            time = datetime.datetime.fromisoformat(time_str)
                            if datetime.datetime.now() >= time:
                                await db.execute("DELETE FROM tempban WHERE guild = ? and member = ? and time = ?",
                                                 (str(guild.id), str(member), time_str))
                                await db.commit()
                                try:
                                    await guild.unban(discord.Object(id=int(member)))
                                except:
                                    await db.execute("DELETE FROM tempban WHERE guild = ? and member = ?",
                                                     (str(guild.id), str(member)))
                                    await db.commit()
                        except:
                            pass
            except:
                pass


class rr:

    @staticmethod
    async def command(inter: MessageCommandInteraction, emoji: str, dir: str, role: str, title: str,
                      description: str) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        await inter.response.send_message("Attempting to create reaction role...", ephemeral=EPHEMERAL)
        async with aiosqlite.connect("rr.db") as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS rr(
            msg_id TEXT,
            emoji UNICODE,
            role TEXT,
            guild TEXT,
            channel TEXT
            )""")
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
                    await db.execute("INSERT INTO rr (msg_id,emoji,role,guild,channel) VALUES (?,?,?,?,?)",
                                     (str(msg.id), x, str(role), str(inter.guild.id), str(inter.channel.id)))
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
                await db.execute("INSERT INTO rr (msg_id,emoji,role,guild,channel) VALUES (?,?,?,?,?)",
                                 (str(msg.id), emoji, str(role), str(inter.guild.id), str(inter.channel.id)))
                await db.commit()
                await inter.followup.send("Successfully created the reaction role.", ephemeral=EPHEMERAL)

    @staticmethod
    async def add(payload: discord.RawReactionActionEvent, dir: str, bot: commands.Bot) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        if payload.guild_id is None:
            return
        if payload.member.bot:
            return
        guild = bot.get_guild(payload.guild_id)
        async with aiosqlite.connect("rr.db") as db:
            try:
                async with db.execute("SELECT emoji,role FROM rr WHERE guild = ? and msg_id = ?",
                                      (str(guild.id), str(payload.message_id))) as cursor:
                    async for entry in cursor:
                        emoji, role = entry
                        role = guild.get_role(int(role))
                        if str(payload.emoji) == emoji:
                            await payload.member.add_roles(role)
            except:
                pass

    @staticmethod
    async def remove(payload: discord.RawReactionActionEvent, dir: str, bot: commands.Bot) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        if payload.guild_id is None:
            return
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member.bot:
            return
        async with aiosqlite.connect("rr.db") as db:
            try:
                async with db.execute("SELECT emoji,role FROM rr WHERE guild = ? and msg_id = ?",
                                      (str(guild.id), str(payload.message_id))) as cursor:
                    async for entry in cursor:
                        emoji, role = entry
                        role = guild.get_role(int(role))
                        if str(payload.emoji) == emoji:
                            await member.remove_roles(role)
            except:
                pass

    @staticmethod
    async def clear_all(inter: MessageCommandInteraction, dir: str) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guild = str(inter.guild.id)
        async with aiosqlite.connect("rr.db") as db:
            try:
                await db.execute("DELETE FROM rr WHERE guild = ?", (guild,))
                await db.commit()
            except:
                return
            msg = "Deleted all reaction role info for this server."
            await inter.response.send_message(msg, ephemeral=EPHEMERAL)

    @staticmethod
    async def clear_one(inter: MessageCommandInteraction, dir: str, message_id: int) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guild = str(inter.guild.id)
        message_id = str(message_id)
        async with aiosqlite.connect("rr.db") as db:
            message_id = message_id.replace(" ", "")
            message_id = message_id.split(",")
            for x in message_id:
                try:
                    await db.execute("DELETE FROM rr WHERE guild = ? and msg_id = ?", (guild, x))
                except:
                    break
            await db.commit()
            message_id = ", ".join(message_id)
            msg = f"Deleted all reaction role info with message ID(s): {message_id}"
            await inter.response.send_message(msg, ephemeral=EPHEMERAL)

    @staticmethod
    async def clear_on_message_delete(message: discord.Message, dir: str) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        if message.guild is None:
            return
        guild = str(message.guild.id)
        id = str(message.id)
        async with aiosqlite.connect("rr.db") as db:
            try:
                async with db.execute("SELECT msg_id FROM rr WHERE guild = ?", (guild,)) as cursor:
                    async for entry in cursor:
                        msg_id = entry[0]
                        if msg_id == id:
                            await db.execute("DELETE FROM rr WHERE msg_id = ? and guild = ?", (msg_id, guild))
                            await db.commit()
                            return
            except:
                pass

    @staticmethod
    async def clear_on_channel_delete(channel: discord.TextChannel, dir: str) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        channel_id = channel.id
        guild = channel.guild.id
        async with aiosqlite.connect("rr.db") as db:
            try:
                async with db.execute("SELECT channel FROM rr WHERE guild = ?", (str(guild),)) as cursor:
                    async for entry in cursor:
                        channel = int(entry[0])
                        if channel == channel_id:
                            await db.execute("DELETE FROM rr WHERE guild = ? and channel = ?",
                                             (str(guild), str(channel)))
                            await db.commit()
                            break
            except:
                pass

    @staticmethod
    async def clear_on_thread_delete(thread: discord.Thread, dir: str) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        thread_id = thread.id
        guild = thread.guild.id
        async with aiosqlite.connect("rr.db") as db:
            try:
                async with db.execute("SELECT channel FROM rr WHERE guild = ?", (str(guild),)) as cursor:
                    async for entry in cursor:
                        channel = int(entry[0])
                        if channel == thread_id:
                            await db.execute("DELETE FROM rr WHERE guild = ? and channel = ?",
                                             (str(guild), str(channel)))
                            await db.commit()
                            break
            except:
                pass

    @staticmethod
    async def clear_on_bulk_message_delete(payload: discord.RawBulkMessageDeleteEvent, dir: str) -> None:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        ids = payload.message_ids
        guild = payload.guild_id
        if guild is None:
            return
        async with aiosqlite.connect("rr.db") as db:
            try:
                async with db.execute("SELECT msg_id FROM rr WHERE guild = ?", (str(guild),)) as cursor:
                    async for entry in cursor:
                        msg_id = int(entry[0])
                        for id in ids:
                            if id == msg_id:
                                await db.execute("DELETE FROM rr WHERE guild = ? and msg_id = ?",
                                                 (str(guild), str(msg_id)))
                await db.commit()
            except:
                pass

    @staticmethod
    async def display(inter: MessageCommandInteraction, dir: str) -> None:
        limit = False
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guild = str(inter.guild.id)
        async with aiosqlite.connect("rr.db") as db:
            embed = discord.Embed(title="5 Most Recent Reaction Roles", color=BLUE)
            try:
                async with db.execute("SELECT msg_id FROM rr WHERE guild = ? GROUP BY msg_id", (guild,)) as cursor:
                    number = 0
                    async for entry in cursor:
                        try:
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
                                    limit = True
                                else:
                                    limit = False
                                    embed.add_field(
                                        name=f"Reaction Role #{number}", inline=False, value=msg)
                        except:
                            continue
                if number > 0:
                    if limit:
                        embed.set_footer(
                            text=f"Total Reaction Roles | {number}")
                        msg = "One of your reaction roles went over the Discord limit. It will still work perfectly but only essential data will be displayed in this command to save space."
                        await inter.followup.send(msg, ephemeral=EPHEMERAL)
                    else:
                        embed.set_footer(
                            text=f"Total Reaction Roles | {number}")
                    await inter.response.send_message(embed=embed, ephemeral=EPHEMERAL)
                else:
                    msg = "There are no reaction roles in this server."
                    await inter.response.send_message(msg, ephemeral=EPHEMERAL)
            except:
                pass
