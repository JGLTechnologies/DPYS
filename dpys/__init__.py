# discord.py is no longer maintained. If there is no new official fork by April 2022, most of DPYS will not work anymore.


# This library is in development and bugs can be expected. If you encounter any bugs, want to give feedback, or would like to contribute, join our Discord server.
# https://discord.gg/TUUbzTa3B7

"""
Copyright (c) 2021 George Luca

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

# Ignore the fact that I used text where there should be an integer in the
# SQL. I made this when I first started and there is not really a point in
# changing it now.

import os
import discord
import datetime
import aiosqlite
import asyncio
from discord.ext import commands
from dpys import utils


RED = 0xD40C00
BLUE = 0x0000FF
GREEN = 0x32C12C
version = "4.4.4"


print("We recommend that you read https://jgltechnologies.com/dpys before you use DPYS.")


class misc:

    async def reload(ctx, bot, cogs, **kwargs):
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
        embed = discord.Embed(
            color=GREEN,
            description=f"**Successfully reloaded {reloaded}/{total} extensions.**")
        await ctx.send(embed=embed, delete_after=7)

    async def clear_data_on_guild_remove(guild, dir):
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
                await db.execute("DELETE FROM mute_roles_info WHERE guild = ?", (str(guild.id),))
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

    async def mute(ctx, member, *args, role_add=1, role_remove=1, reason=None, **kwargs):
        if ctx.guild.get_role(role_add) in member.roles:
            embed = discord.Embed(
                color=RED,
                description=f"**{member.name}#{member.discriminator} is already muted.**")
            await ctx.send(embed=embed, delete_after=5)
            return
        if len(str(reason)) >= 256:
            embed = discord.Embed(
                color=RED, description=f"**That reason is too long.**")
            await ctx.send(embed=embed, delete_after=5)
            return
        else:
            if not isinstance(ctx.guild.get_role(role_add), discord.Role):
                return
            await member.add_roles(ctx.guild.get_role(role_add))
            if role_remove != 1:
                try:
                    await member.remove_roles(ctx.guild.get_role(role_remove))
                except:
                    pass
            if reason is None:
                embed = discord.Embed(
                    color=GREEN, description=f"**Muted {member.name}#{member.discriminator}.**")
                await ctx.send(embed=embed, delete_after=7)
            else:
                embed = discord.Embed(
                    color=GREEN,
                    description=f"**Muted {member.name}#{member.discriminator}. Reason: {reason}**")
                await ctx.send(embed=embed, delete_after=7)

    async def unmute(ctx, member, *args, role_add=1, role_remove=1, **kwargs):
        if ctx.guild.get_role(role_remove) not in member.roles:
            embed = discord.Embed(
                color=RED,
                description=f"**{member.name}#{member.discriminator} is not muted.**")
            await ctx.send(embed=embed, delete_after=5)
            return
        else:
            if not isinstance(ctx.guild.get_role(role_remove), discord.Role):
                return
            await member.remove_roles(ctx.guild.get_role(role_remove))
            if role_add != 1:
                try:
                    await member.add_roles(ctx.guild.get_role(role_add))
                except:
                    pass
            embed = discord.Embed(
                color=GREEN,
                description=f"**Unmuted {member.name}#{member.discriminator}.**")
            await ctx.send(embed=embed, delete_after=7)

    async def clear(ctx, amount=None):
        if amount is None:
            amount = 99999999999999999
        else:
            amount = int(amount)
        limit = datetime.datetime.now() - datetime.timedelta(weeks=2)
        await ctx.message.delete()
        purged = await ctx.channel.purge(limit=amount, after=limit)
        purged = len(purged)
        if purged != 1:
            embed = discord.Embed(
                color=GREEN, description=f"**Cleared {purged} messages.**")
        else:
            embed = discord.Embed(color=GREEN,
                                  description=f"**Cleared {purged} message.**")
        await ctx.send(embed=embed, delete_after=5)
        return purged

    async def kick(ctx, member, reason=None):
        if len(str(reason)) >= 256:
            embed = discord.Embed(
                color=RED, description=f"**That reason is too long.**")
            await ctx.send(embed=embed, delete_after=5)
            return
        await member.kick(reason=reason)
        if reason is None:
            embed = discord.Embed(
                color=GREEN,
                description=f"**Kicked {member.name}#{member.discriminator}.**")
            await ctx.send(embed=embed, delete_after=7)
        else:
            embed = discord.Embed(
                color=GREEN,
                description=f"**Kicked {member.name}#{member.discriminator}. Reason: {reason}**")
            await ctx.send(embed=embed, delete_after=7)

    async def ban(ctx, member, reason=None):
        if len(str(reason)) >= 256:
            embed = discord.Embed(
                color=RED, description=f"**That reason is too long.**")
            await ctx.send(embed=embed, delete_after=5)
            return
        await member.ban(reason=reason)
        if reason is None:
            embed = discord.Embed(
                color=GREEN,
                description=f"**Banned {member.name}#{member.discriminator}.**")
            await ctx.send(embed=embed, delete_after=7)
        else:
            embed = discord.Embed(
                color=GREEN,
                description=f"**Banned {member.name}#{member.discriminator}. Reason: {reason}**")
            await ctx.send(embed=embed, delete_after=7)

    async def softban(ctx, member, reason=None):
        if len(str(reason)) >= 256:
            embed = discord.Embed(
                color=RED, description=f"**That reason is too long.**")
            await ctx.send(embed=embed, delete_after=5)
            return
        await member.ban(reason=reason)
        if reason is None:
            embed = discord.Embed(
                color=GREEN,
                description=f"**Soft banned {member.name}#{member.discriminator}.**")
            await ctx.send(embed=embed, delete_after=7)
        else:
            embed = discord.Embed(
                color=GREEN,
                description=f"**Soft banned {member.name}#{member.discriminator}. Reason: {reason}**")
            await ctx.send(embed=embed, delete_after=7)
        await member.unban()

    async def unban(ctx, member):
        bans = await ctx.guild.bans()
        if await utils.var_can_be_type(member, int):
            ban = [ban for ban in bans if ban.user.id == int(member)]
        else:
            name, discrim = member.split("#")
            ban = [ban for ban in bans if ban.user.discriminator ==
                   discrim and ban.user.name == name]
        if ban == []:
            embed = discord.Embed(
                color=RED, description=f"**{member} is not banned.**")
            await ctx.send(embed=embed, delete_after=5)
            return
        await ctx.guild.unban(ban[0].user)
        embed = discord.Embed(color=RED, description=f"**Unbanned {member}.**")
        await ctx.send(embed=embed, delete_after=7)


class curse:

    async def add_banned_word(ctx, word, dir):
        arg = word
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        word = word.lower()
        guildid = str(ctx.guild.id)
        async with aiosqlite.connect("curse.db") as db:
            await db.execute(f"""CREATE TABLE if NOT EXISTS curses(
            curse TEXT,
            guild TEXT,
            PRIMARY KEY (curse,guild)
            )""")
            await db.commit()
            words = word.replace(" ", "")
            words = words.split(",")
            curses = await utils.GuildData.curse_set(ctx.guild.id, dir)
            for x in words:
                if x in curses:
                    if "," in arg:
                        msg = f"**One of those words are already in the list.**"
                    else:
                        msg = f"**That word is already in the list.**"
                    embed = discord.Embed(color=RED, description=msg)
                    await ctx.send(embed=embed, delete_after=5)
                    return
                for x in words:
                    if words.count(x) > 1:
                        embed = discord.Embed(
                            color=RED, description="**Words cannot be added twice.**")
                        await ctx.send(embed=embed, delete_after=5)
                        return
                    await db.execute("INSERT INTO curses (curse,guild) VALUES (?,?)", (x, guildid))
                await db.commit()
            embed = discord.Embed(color=GREEN,
                                  description="**Added word(s) the list.**")
            await ctx.send(embed=embed, delete_after=7)

    async def remove_banned_word(ctx, word, dir):
        async with aiosqlite.connect("curse.db") as db:
            guildid = str(ctx.guild.id)
            await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
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
                if in_db == False:
                    if len(word) > 1:
                        embed = discord.Embed(
                            color=RED, description="**None of those words are in the list.**")
                        await ctx.send(embed=embed, delete_after=5)
                    else:
                        embed = discord.Embed(
                            color=RED, description="**That word is not in the list.**")
                        await ctx.send(embed=embed, delete_after=5)
                    return
                for x in word:
                    await db.execute("DELETE FROM curses WHERE curse = ? and guild = ?", (x, guildid))
                    await db.commit()
                embed = discord.Embed(
                    color=GREEN, description="**Removed word(s) from the list.**")
                await ctx.send(embed=embed, delete_after=5)
            except:
                embed = discord.Embed(
                    color=RED, description="**A list has not been created yet.**")
                await ctx.send(embed=embed, delete_after=5)

    async def message_filter(message, dir, admin: int = 1):
        if message.author.bot or message.guild is None:
            return
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guildid = str(message.guild.id)
        if admin != 1:
            adminrole = message.guild.get_role(admin)
            if adminrole in message.author.roles or message.author.top_role.position > adminrole.position or message.author.bot:
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

    async def message_edit_filter(after, dir, admin: int = 1):
        message = after
        if message.author.bot or message.guild is None:
            return
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guildid = str(message.guild.id)
        if message.author.bot:
            return
        else:
            if admin != 1:
                adminrole = message.guild.get_role(admin)
                if adminrole in message.author.roles or message.author.top_role.position > adminrole.position or message.author.bot:
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

    async def clear_words(ctx, dir):
        guildid = str(ctx.guild.id)
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        try:
            async with aiosqlite.connect("curse.db") as db:
                await db.execute("DELETE FROM curses WHERE guild = ?", (guildid,))
                await db.commit()
                await ctx.send("Cleared all curses from this server", delete_after=7)
        except:
            embed = discord.Embed(
                color=RED,
                description="**There is not a curse list for this server. Create one by doing !addword followed by a list of words or a single word.**")
            await ctx.send(embed=embed, delete_after=5)


class mute_on_join:

    async def mute_add(guild, member, dir):
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guildid = str(guild.id)
        member = str(member.id)
        try:
            async with aiosqlite.connect("muted.db") as db:
                await db.execute(f"""CREATE TABLE if NOT EXISTS muted(
                name TEXT PRIMARY KEY,
                guild TEXT
                )""")
                await db.commit()
                await db.execute("INSERT INTO muted (name,guild) VALUES (?,?)", (member, guildid))
                await db.commit()
        except:
            pass

    async def mute_remove(guild, member, dir):
        member = str(member.id)
        guildid = str(guild.id)
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        try:
            async with aiosqlite.connect("muted.db") as db:
                await db.execute("DELETE FROM muted WHERE name = ? and guild = ?", (member, guildid))
                await db.commit()
        except:
            pass

    async def mute_on_join(member, role, dir):
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

    async def manual_unmute_check(after, roleid, dir):
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

    async def warn(ctx, member, dir, reason=None):
        if len(str(reason)) >= 256:
            embed = discord.Embed(
                color=RED, description=f"**That reason is too long.**")
            await ctx.send(embed=embed, delete_after=5)
            return
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        reason_str = str(reason)
        guildid = str(ctx.guild.id)
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
            await db.execute("INSERT INTO warnings (member_id,guild,reason) VALUES (?,?,?)", (member, guildid, reason_str))
            await db.commit()
            if reason is None:
                embed = discord.Embed(
                    color=GREEN, description=f"**Warned {user.name}#{user.discriminator}.**")
                await ctx.send(embed=embed, delete_after=7)
            else:
                embed = discord.Embed(
                    color=GREEN,
                    description=f"**Warned {user.name}#{user.discriminator}. Reason: {reason}**")
                await ctx.send(embed=embed, delete_after=7)

    async def warnings_list(ctx, member, dir):
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guildid = str(ctx.guild.id)
        user = member
        member = str(member.id)
        try:
            async with aiosqlite.connect("warnings.db") as db:
                async with db.execute("SELECT reason FROM warnings WHERE guild = ? and member_id = ?", (guildid, member)) as cursor:
                    embed = discord.Embed(
                        color=BLUE, title=f"{user.name}#{user.discriminator}'s Warnings")
                    number = 0
                    async for entry in cursor:
                        number += 1
                        embed.add_field(
                            name=f"#{number} warning",
                            value=f"Reason: {entry[0]}",
                            inline=False)
                    if number > 0:
                        embed.set_footer(text=f"Total Warnings | {number}")
                        await ctx.send(embed=embed)
                    else:
                        embed = discord.Embed(
                            color=RED, description=f"**{user.name}#{user.discriminator} has no warnings.**")
                        await ctx.send(embed=embed, delete_after=5)
        except:
            embed = discord.Embed(
                color=RED,
                description=f"**{user.name}#{user.discriminator} has no warnings.**")
            await ctx.send(embed=embed, delete_after=5)

    async def unwarn(ctx, member, dir, number):
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        user = member
        guild = str(ctx.guild.id)
        member = str(member.id)
        number = str(number)
        number = number.lower()
        async with aiosqlite.connect("warnings.db") as db:
            try:
                async with db.execute("SELECT reason FROM warnings WHERE guild = ? and member_id = ?", (guild, member)) as cursor:
                    count = 0
                    async for entry in cursor:
                        count += 1
            except:
                embed = discord.Embed(
                    color=RED, description=f"**{user.name}#{user.discriminator} has no warnings.**")
                await ctx.send(embed=embed, delete_after=5)
                return
            if count < 1:
                embed = discord.Embed(
                    color=RED, description=f"**{user.name}#{user.discriminator} has no warnings.**")
                await ctx.send(embed=embed, delete_after=5)
                return
            if number == "all":
                await db.execute("DELETE FROM warnings WHERE guild = ? and member_id = ?", (guild, member))
                await db.commit()
                embed = discord.Embed(
                    color=GREEN,
                    description=f"**Cleared all warnings from {user.name}#{user.discriminator}.**")
                await ctx.send(embed=embed, delete_after=7)
                return
            else:
                try:
                    if "," in number:
                        number = number.replace(" ", "")
                        number_list = number.split(",")
                        number_list = list(map(int, number_list))
                        number_list = sorted(number_list, reverse=True)
                        dict = {}
                        async with db.execute("SELECT id,row_number() OVER (ORDER BY id) FROM warnings WHERE guild = ? and member_id = ?", (guild, member)) as cursor:
                            async for entry in cursor:
                                id, pos = entry
                                pos = str(pos)
                                dict.update({pos: id})
                        for x in number_list:
                            await db.execute("DELETE FROM warnings WHERE id = ?", (dict[str(x)],))
                        await db.commit()
                        number_list = list(map(str, number_list))
                        number_list = ", ".join(number_list)
                        await ctx.send(f"Cleared warnings {number_list} from {user.mention}.", delete_after=7)
                        embed = discord.Embed(
                            color=GREEN,
                            description=f"**Cleared warnings {number_list} from .{user.name}#{user.discriminator}.**")
                        await ctx.send(embed=embed, delete_after=7)
                    else:
                        number = int(number)
                        dict = {}
                        async with db.execute("SELECT id,row_number() OVER (ORDER BY id) FROM warnings WHERE guild = ? and member_id = ?", (guild, member)) as cursor:
                            async for entry in cursor:
                                id, pos = entry
                                pos = str(pos)
                                dict.update({pos: id})
                        await db.execute("DELETE FROM warnings WHERE id = ?", (dict[str(number)],))
                        await db.commit()
                        embed = discord.Embed(
                            color=GREEN,
                            description=f"**Cleared {user.name}#{user.discriminator}'s #{number} warning.**")
                        await ctx.send(embed=embed, delete_after=7)
                except:
                    if number == "all":
                        embed = discord.Embed(
                            color=RED, description=f"**{user.name}#{user.discriminator} has no warnings.**")
                        await ctx.send(embed=embed, delete_after=5)
                    else:
                        embed = discord.Embed(
                            color=RED,
                            description=f"**{user.name}#{user.discriminator} does not have that many warnings.**")
                        await ctx.send(embed=embed, delete_after=5)

    async def punish(ctx, member, dir, *args, one=None, two=None, three=None, four=None, five=None, six=None, seven=None, eight=None, nine=None, ten=None, eleven=None, twelve=None, thirteen=None, fourteen=None, fifteen=None, remove_role=None, add_role=None, **kwargs):
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        memberid = str(member.id)
        guild = str(ctx.guild.id)
        async with aiosqlite.connect("warnings.db") as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS tempmute(
                        guild TEXT,
                        member TEXT,
                        time DATETIME
                        )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS mute_roles_info(
                        guild TEXT PRIMARY KEY,
                        role_add TEXT,
                        role_remove TEXT
                        )""")
            try:
                await db.execute("INSERT INTO mute_roles_info (guild,role_add,role_remove) VALUES (?,?,?)", (guild, str(add_role), str(remove_role)))
            except:
                await db.execute("UPDATE mute_roles_info SET role_add = ?, role_remove = ? WHERE guild = ?", (str(add_role), str(remove_role), guild))
            await db.execute("""CREATE TABLE IF NOT EXISTS tempban(
                        guild TEXT,
                        member TEXT,
                        time DATETIME
                        )""")
            await db.commit()
            try:
                async with db.execute("SELECT reason FROM warnings WHERE guild = ? and member_id = ?", (guild, memberid)) as cursor:
                    warnings_number = 0
                    async for _ in cursor:
                        warnings_number += 1
            except:
                return
            if warnings_number == 1:
                warnings_number_str = one
                message = "You received your first warning."
            if warnings_number == 2:
                warnings_number_str = two
                message = "You received your second warning."
            if warnings_number == 3:
                warnings_number_str = three
                message = "You received your third warning."
            if warnings_number == 4:
                warnings_number_str = four
                message = "You received your fourth warning."
            if warnings_number == 5:
                warnings_number_str = five
                message = "You received your fith warning."
            if warnings_number == 6:
                warnings_number_str = six
                message = "You received your sixth warning."
            if warnings_number == 7:
                warnings_number_str = seven
                message = "You received your seventh warning."
            if warnings_number == 8:
                warnings_number_str = eight
                message = "You received your eighth warning."
            if warnings_number == 9:
                warnings_number_str = nine
                message = "You received your ninth warning."
            if warnings_number == 10:
                warnings_number_str = ten
                message = "You received your tenth warning."
            if warnings_number == 11:
                warnings_number_str = eleven
                message = "You received your eleventh warning."
            if warnings_number == 12:
                warnings_number_str = twelve
                message = "You received your twelfth warning."
            if warnings_number == 13:
                warnings_number_str = thirteen
                message = "You received your thirteenth warning."
            if warnings_number == 14:
                warnings_number_str = fourteen
                message = "You received your fourteenth warning."
            if warnings_number == 15:
                warnings_number_str = fifteen
                message = "You received your fifteenth warning."
            if warnings_number_str is None:
                return
            if "temp" in warnings_number_str:
                pun_time = warnings_number_str[5:]
                pun, time = pun_time.split("_")
                time = time.lower()
                if pun == "ban":
                    if "s" in time:
                        time = int(time[:-1])
                        await member.ban(reason=message)
                        time = datetime.datetime.now() + datetime.timedelta(seconds=time)
                        await db.execute("INSERT INTO tempban (guild,member,time) VALUES (?,?,?)", (guild, memberid, time))
                        await db.commit()
                        return
                    if "m" in time:
                        time = int(time[:-1])
                        await member.ban(reason=message)
                        time = datetime.datetime.now() + datetime.timedelta(minutes=time)
                        await db.execute("INSERT INTO tempban (guild,member,time) VALUES (?,?,?)", (guild, memberid, time))
                        await db.commit()
                        return
                    if "h" in time:
                        time = int(time[:-1])
                        await member.ban(reason=message)
                        time = datetime.datetime.now() + datetime.timedelta(hours=time)
                        await db.execute("INSERT INTO tempban (guild,member,time) VALUES (?,?,?)", (guild, memberid, time))
                        await db.commit()
                        return
                    if "d" in time:
                        time = int(time[:-1])
                        await member.ban(reason=message)
                        time = datetime.datetime.now() + datetime.timedelta(days=time)
                        await db.execute("INSERT INTO tempban (guild,member,time) VALUES (?,?,?)", (guild, memberid, time))
                        await db.commit()
                        return
                else:
                    add_role = ctx.guild.get_role(add_role)
                    if not isinstance(add_role, discord.Role):
                        return
                    remove_role = ctx.guild.get_role(remove_role)
                    if not isinstance(remove_role, discord.Role):
                        remove_role = None
                    if remove_role is not None:
                        if add_role in member.roles:
                            return
                        else:
                            if "s" in time:
                                time = int(time[:-1])
                                await member.add_roles(add_role)
                                await member.remove_roles(remove_role)
                                await mute_on_join.mute_add(ctx.guild, member, dir)
                                time = datetime.datetime.now() + datetime.timedelta(seconds=time)
                                await db.execute("INSERT INTO tempmute (guild,member,time) VALUES (?,?,?)", (guild, memberid, time))
                                await db.commit()
                                return
                            if "m" in time:
                                time = int(time[:-1])
                                await member.add_roles(add_role)
                                await member.remove_roles(remove_role)
                                await mute_on_join.mute_add(ctx.guild, member, dir)
                                time = datetime.datetime.now() + datetime.timedelta(minutes=time)
                                await db.execute("INSERT INTO tempmute (guild,member,time) VALUES (?,?,?)", (guild, memberid, time))
                                await db.commit()
                                return
                            if "h" in time:
                                time = int(time[:-1])
                                await member.add_roles(add_role)
                                await member.remove_roles(remove_role)
                                await mute_on_join.mute_add(ctx.guild, member, dir)
                                time = datetime.datetime.now() + datetime.timedelta(hours=time)
                                await db.execute("INSERT INTO tempmute (guild,member,time) VALUES (?,?,?)", (guild, memberid, time))
                                await db.commit()
                                return
                            if "d" in time:
                                time = int(time[:-1])
                                await member.add_roles(add_role)
                                await member.remove_roles(remove_role)
                                await mute_on_join.mute_add(ctx.guild, member, dir)
                                time = datetime.datetime.now() + datetime.timedelta(days=time)
                                await db.execute("INSERT INTO tempmute (guild,member,time) VALUES (?,?,?)", (guild, memberid, time))
                                await db.commit()
                                return
                    else:
                        if "s" in time:
                            time = int(time[:-1])
                            await member.add_roles(add_role)
                            await mute_on_join.mute_add(ctx.guild, member, dir)
                            time = datetime.datetime.now() + datetime.timedelta(seconds=time)
                            await db.execute("INSERT INTO tempmute (guild,member,time) VALUES (?,?,?)", (guild, memberid, time))
                            await db.commit()
                            return
                        if "m" in time:
                            time = int(time[:-1])
                            await member.add_roles(add_role)
                            await mute_on_join.mute_add(ctx.guild, member, dir)
                            time = datetime.datetime.now() + datetime.timedelta(minutes=time)
                            await db.execute("INSERT INTO tempmute (guild,member,time) VALUES (?,?,?)", (guild, memberid, time))
                            await db.commit()
                            return
                        if "h" in time:
                            time = int(time[:-1])
                            await member.add_roles(add_role)
                            await mute_on_join.mute_add(ctx.guild, member, dir)
                            time = datetime.datetime.now() + datetime.timedelta(hours=time)
                            await db.execute("INSERT INTO tempmute (guild,member,time) VALUES (?,?,?)", (guild, memberid, time))
                            await db.commit()
                            return
                        if "d" in time:
                            time = int(time[:-1])
                            await member.add_roles(add_role)
                            await mute_on_join.mute_add(ctx.guild, member, dir)
                            time = datetime.datetime.now() + datetime.timedelta(days=time)
                            await db.execute("INSERT INTO tempmute (guild,member,time) VALUES (?,?,?)", (guild, memberid, time))
                            await db.commit()
                            return
            else:
                if warnings_number_str == "ban":
                    await member.ban(reason=message)
                    return
                if warnings_number_str == "kick":
                    await member.kick(reason=message)
                    return
                if warnings_number_str == "mute":
                    add_role = ctx.guild.get_role(add_role)
                    try:
                        remove_role = ctx.guild.get_role(remove_role)
                    except:
                        remove_role = None
                    if remove_role is not None:
                        if add_role in member.roles:
                            return
                        else:
                            await member.add_roles(add_role)
                            await member.remove_roles(remove_role)
                            await mute_on_join.mute_add(ctx.guild, member, dir)
                    else:
                        await member.add_roles(add_role)
                        await mute_on_join.mute_add(ctx.guild, member, dir)

    async def temp_mute_loop(dir, bot):
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
                            member = guild.get_member(int(member))
                            if not isinstance(member, discord.Member):
                                await db.execute("DELETE FROM tempmute WHERE guild = ? and member = ?", (str(guild_id), str(member_id)))
                                await db.commit()
                                continue
                            time = datetime.datetime.fromisoformat(time_str)
                            async with db.execute("SELECT role_add FROM mute_roles_info WHERE guild = ?", (str(guild.id),)) as role_add_cursor:
                                role_add = await role_add_cursor.fetchone()
                            async with db.execute("SELECT role_remove FROM mute_roles_info WHERE guild = ?", (str(guild.id),)) as role_remove_cursor:
                                role_remove = await role_remove_cursor.fetchone()
                            if datetime.datetime.now() >= time:
                                if role_remove != "None" and role_remove != "none":
                                    try:
                                        await member.add_roles(guild.get_role(int(role_remove)))
                                    except:
                                        pass
                                try:
                                    await member.remove_roles(guild.get_role(int(role_add)))
                                except:
                                    pass
                                await db.execute("DELETE FROM tempmute WHERE guild = ? and member = ? and time = ?", (str(guild.id), str(member.id), time_str))
                                await db.commit()
                                await mute_on_join.mute_remove(guild, member, dir)
                        except:
                            continue
            except:
                pass

    async def temp_ban_loop(dir, bot):
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
                                await db.execute("DELETE FROM tempban WHERE guild = ? and member = ? and time = ?", (str(guild.id), str(member), time_str))
                                await db.commit()
                                try:
                                    await guild.unban(discord.Object(id=int(member)))
                                except:
                                    await db.execute("DELETE FROM tempban WHERE guild = ? and member = ?", (str(guild.id), str(member)))
                                    await db.commit()
                        except:
                            pass
            except:
                pass


class rr:

    async def command(ctx, emoji, dir, role, *args, title, description, **kwargs):
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
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
            if "," in role:
                emoji = emoji.replace(" ", "")
                emoji_list = emoji.split(",")
                role = role.replace(" ", "")
                role_list = role.split(",")
                if len(role_list) != len(emoji_list):
                    await ctx.send("Emoji list must be same length as role list.", delete_after=5)
                    return
            if "," in emoji:
                emoji = emoji.replace(" ", "")
                emoji_list = emoji.split(",")
                role = role.replace(" ", "")
                role_list = role.split(",")
                if len(role_list) != len(emoji_list):
                    await ctx.send("Emoji list must be same length as role list.", delete_after=5)
                    return
                for x in role_list:
                    role = role.replace("<", "")
                    role = role.replace(">", "")
                    role = role.replace("@", "")
                    role = role.replace("&", "")
                    try:
                        if ctx.guild.get_role(int(role)) is None:
                            embed = discord.Embed(
                                color=RED, description="**Invalid Role**")
                            await ctx.send(embed=embed, delete_after=5)
                            return
                    except:
                        embed = discord.Embed(
                            color=RED, description="**Invalid Role**")
                        await ctx.send(embed=embed, delete_after=5)
                        return
                msg = await ctx.send(embed=embed)
                number = 0
                for x in emoji_list:
                    role = role_list[number]
                    if "@" not in role:
                        embed = discord.Embed(
                            color=RED, description="**Invalid Role**")
                        await ctx.send(embed=embed, delete_after=5)
                        return
                    number += 1
                    await msg.add_reaction(x)
                    await db.execute("INSERT INTO rr (msg_id,emoji,role,guild,channel) VALUES (?,?,?,?,?)", (str(msg.id), x, str(role), str(ctx.guild.id), str(ctx.channel.id)))
                await db.commit()
            else:
                if "@" not in role:
                    embed = discord.Embed(
                        color=RED, description="**Invalid Role**")
                    await ctx.send(embed=embed, delete_after=5)
                    return
                role = role.replace("<", "")
                role = role.replace(">", "")
                role = role.replace("@", "")
                role = role.replace("&", "")
                try:
                    if ctx.guild.get_role(int(role)) is None:
                        embed = discord.Embed(
                            color=RED, description="**Invalid Role**")
                        await ctx.send(embed=embed, delete_after=5)
                        return
                except:
                    embed = discord.Embed(
                        color=RED, description="**Invalid Role**")
                    await ctx.send(embed=embed, delete_after=5)
                    return
                msg = await ctx.send(embed=embed)
                await msg.add_reaction(emoji)
                await db.execute("INSERT INTO rr (msg_id,emoji,role,guild,channel) VALUES (?,?,?,?,?)", (str(msg.id), emoji, str(role), str(ctx.guild.id), str(ctx.channel.id)))
                await db.commit()

    async def add(payload, dir, client):
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        if payload.guild_id is None:
            return
        if payload.member.bot:
            return
        guild = client.get_guild(payload.guild_id)
        async with aiosqlite.connect("rr.db") as db:
            try:
                async with db.execute("SELECT emoji,role FROM rr WHERE guild = ? and msg_id = ?", (str(guild.id), str(payload.message_id))) as cursor:
                    async for entry in cursor:
                        emoji, role = entry
                        role = guild.get_role(int(role))
                        if str(payload.emoji) == emoji:
                            await payload.member.add_roles(role)
            except:
                pass

    async def remove(payload, dir, client):
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        if payload.guild_id is None:
            return
        guild = client.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member.bot:
            return
        async with aiosqlite.connect("rr.db") as db:
            try:
                async with db.execute("SELECT emoji,role FROM rr WHERE guild = ? and msg_id = ?", (str(guild.id), str(payload.message_id))) as cursor:
                    async for entry in cursor:
                        emoji, role = entry
                        role = guild.get_role(int(role))
                        if str(payload.emoji) == emoji:
                            await member.remove_roles(role)
            except:
                pass

    async def clear_all(ctx, dir):
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guild = str(ctx.guild.id)
        async with aiosqlite.connect("rr.db") as db:
            try:
                await db.execute("DELETE FROM rr WHERE guild = ?", (guild,))
                await db.commit()
            except:
                return
            embed = discord.Embed(
                color=GREEN,
                description="**Deleted all reaction role info for this server.**")
            await ctx.send(embed=embed, delete_after=7)

    async def clear_one(ctx, dir, message_id):
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guild = str(ctx.guild.id)
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
            embed = discord.Embed(
                color=GREEN,
                description=f"**Delted all reaction role info with message ID(s): {message_id}**")
            await ctx.send(embed=embed, delete_after=7)

    async def clear_on_message_delete(message, dir):
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

    async def clear_on_channel_delete(channel, dir):
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        channel_id = channel.id
        guild = channel.guild.id
        async with aiosqlite.connect("rr.db") as db:
            try:
                async with db.execute("SELECT channel FROM rr WHERE guild = ?", (str(guild),)) as cursor:
                    async for entry in cursor:
                        channel = int(entry[0])
                        if channel == channel_id:
                            await db.execute("DELETE FROM rr WHERE guild = ? and channel = ?", (str(guild), str(channel)))
                            await db.commit()
                            break
            except:
                pass

    async def clear_on_bulk_message_delete(payload, dir):
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
                                await db.execute("DELETE FROM rr WHERE guild = ? and msg_id = ?", (str(guild), str(msg_id)))
                await db.commit()
            except:
                pass

    async def display(ctx, dir):
        limit = "limit"
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        guild = str(ctx.guild.id)
        async with aiosqlite.connect("rr.db") as db:
            embed = discord.Embed(title="Reaction Roles", color=BLUE)
            try:
                async with db.execute("SELECT msg_id FROM rr WHERE guild = ? GROUP BY msg_id", (guild,)) as cursor:
                    number = 0
                    async for entry in cursor:
                        try:
                            async with db.execute("SELECT role,emoji,channel,msg_id FROM rr WHERE guild = ? and msg_id = ?", (guild, entry[0])) as f:
                                msg = ""
                                msg_limit = ""
                                async for entry in f:
                                    role, emoji, channel, msg_id = entry
                                    channel = ctx.guild.get_channel(
                                        int(channel))
                                    role = ctx.guild.get_role(int(role))
                                    try:
                                        role = f"@{role.name}"
                                    except:
                                        role = "@deleted-role"
                                    try:
                                        channel = f"#{channel.name}"
                                    except:
                                        channel = "#deleted-channel"
                                    msg += f"Emoji: {emoji} Role: {role}\n"
                                msg_limit += f"Channel: {channel} Message ID: {msg_id}\n"
                                msg += f"Channel: {channel} Message ID: {msg_id}\n"
                                number += 1
                            if len(msg) > 1010:
                                embed.add_field(
                                    name=f"Reaction Role #{number}", inline=False, value=msg_limit)
                                limit = "True"
                            else:
                                embed.add_field(
                                    name=f"Reaction Role #{number}", inline=False, value=msg)
                        except:
                            continue
                if number > 0:
                    if limit == "limit":
                        embed.set_footer(
                            text=f"Total Reaction Roles | {number}")
                    else:
                        embed.set_footer(
                            text=f"Total Reaction Roles | {number}")
                        limit_embed = discord.Embed(
                            color=RED,
                            description="One of your reaction roles went over the Discord limit. It will still work perfectly but only essential data will be displayed in this command to save space.")
                        await ctx.reply(embed=limit_embed, delete_after=7)
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        color=RED, description="**There are no reaction roles in this server.**")
                    await ctx.send(embed=embed, delete_after=5)
            except:
                pass
