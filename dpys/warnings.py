import contextlib
import datetime
import math
import sqlite3
import time
import typing
from typing import Awaitable, Callable, List, Optional

import disnake
import disnake as discord
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

import dpys
from .mute_on_join import mute_on_join
from .utils import ListScroller


class warnings:
    @staticmethod
    async def _run_before(
        before: Optional[
            Callable[
                [int, "warnings.Punishment", discord.Member],
                Awaitable[Optional[discord.Message]],
            ]
        ],
        warnings_number: int,
        punishment: "warnings.Punishment",
        member: discord.Member,
    ) -> Optional[discord.Message]:
        if before is None:
            return None
        return await before(warnings_number, punishment, member)

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
            if not punishment.startswith("temp") and punishment != "timeout":
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
        db = dpys.warnings_db
        if len(str(reason)) > 256:
            reason = reason[:253] + "..."
        reason_str = str(reason)
        guildid = str(inter.guild.id)
        user = member
        member_id = str(member.id)
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
            (member_id, guildid, reason_str, expires),
        ):
            pass
        await db.commit()
        if reason is None:
            msg = f"Warned {user.display_name}."
        else:
            msg = f"Warned {user.display_name}. Reason: {reason}"
        await inter.send(msg, ephemeral=dpys.EPHEMERAL)

    @staticmethod
    async def warnings_list(guild: int, member_id: int) -> List[str]:
        db = dpys.warnings_db
        try:
            async with db.execute(
                "SELECT reason FROM warnings WHERE guild = ? and member_id = ? ORDER BY id",
                (str(guild), str(member_id)),
            ) as cursor:
                warn_list = []
                async for entry in cursor:
                    warn_list.append(entry[0])
                return warn_list
        except Exception:
            return []

    @staticmethod
    async def warnings(
        inter: ApplicationCommandInteraction, member: discord.Member, warn_num: int = 0
    ) -> None:
        guildid = str(inter.guild.id)
        user = member
        member_id = str(member.id)
        db = dpys.warnings_db
        try:
            async with db.execute(
                "SELECT reason FROM warnings WHERE guild = ? and member_id = ? ORDER BY id",
                (guildid, member_id),
            ) as cursor:
                number = 0
                warn_list = []
                async for entry in cursor:
                    number += 1
                    warn_list.append(entry[0])
                if number > 0:
                    if warn_num == 0:
                        def func(array, start_num, page_info):
                            embed = disnake.Embed(
                                title=f"{user.display_name}'s Warnings",
                                color=dpys.COLOR,
                            )
                            for i, warning in enumerate(array):
                                embed.add_field(
                                    name=f"Warning #{i + start_num}",
                                    value=f"Reason: {warning}",
                                    inline=False,
                                )
                            embed.set_footer(
                                text=f"Page {page_info[0]}/{page_info[1]} | Total Warnings: {number}"
                            )
                            return embed

                        view = ListScroller(5, warn_list, func, inter)
                        embed = func(
                            warn_list[0:5], 1, (1, math.ceil(len(warn_list) / 5))
                        )
                        await view.start()
                        await inter.send(
                            embed=embed, view=view, ephemeral=dpys.EPHEMERAL
                        )
                    else:
                        embed = discord.Embed(
                            color=dpys.COLOR, title=f"{user.display_name}'s Warnings"
                        )
                        if warn_num > len(warn_list):
                            await inter.send(
                                f"{user.display_name} does not have that many.",
                                ephemeral=dpys.EPHEMERAL,
                            )
                            return
                        embed.add_field(
                            name=f"Warning #{warn_num}",
                            value=f"Reason: {warn_list[warn_num - 1]}",
                            inline=False,
                        )
                        embed.set_footer(text=f"Total Warnings: {number}")
                        await inter.send(embed=embed, ephemeral=dpys.EPHEMERAL)
                else:
                    await inter.send(
                        f"{user.display_name} has no warnings.",
                        ephemeral=dpys.EPHEMERAL,
                    )
        except sqlite3.OperationalError:
            await inter.send(
                f"{user.display_name} has no warnings.", ephemeral=dpys.EPHEMERAL
            )

    @staticmethod
    async def unwarn(
        inter: ApplicationCommandInteraction, member, number: typing.Union[int, str]
    ) -> bool:
        user = member
        guild = str(inter.guild.id)
        member_id = str(member.id)
        number = str(number).lower()
        db = dpys.warnings_db
        try:
            async with db.execute(
                "SELECT reason FROM warnings WHERE guild = ? and member_id = ? ORDER BY id",
                (guild, member_id),
            ) as cursor:
                count = 0
                async for _ in cursor:
                    count += 1
        except Exception:
            await inter.send(
                f"{user.display_name} has no warnings.", ephemeral=dpys.EPHEMERAL
            )
            return False
        if count < 1:
            await inter.send(
                f"{user.display_name} has no warnings.", ephemeral=dpys.EPHEMERAL
            )
            return False
        if number == "all":
            async with db.execute(
                "DELETE FROM warnings WHERE guild = ? and member_id = ?",
                (guild, member_id),
            ):
                pass
            await db.commit()
            await inter.send(
                f"Cleared all warnings from {user.display_name}.",
                ephemeral=dpys.EPHEMERAL,
            )
            return True
        try:
            if "," in number:
                number_list = sorted(
                    list(map(int, number.replace(" ", "").split(","))), reverse=True
                )
                rows = {}
                async with db.execute(
                    "SELECT id,row_number() OVER (ORDER BY id) FROM warnings WHERE guild = ? and member_id = ?",
                    (guild, member_id),
                ) as cursor:
                    async for entry in cursor:
                        warning_id, pos = entry
                        rows[str(pos)] = warning_id
                for item in number_list:
                    async with db.execute(
                        "DELETE FROM warnings WHERE id = ?", (rows[str(item)],)
                    ):
                        pass
                await db.commit()
                await inter.send(
                    f"Cleared warnings {', '.join(map(str, number_list))} from {user.display_name}.",
                    ephemeral=dpys.EPHEMERAL,
                )
            else:
                number_int = int(number)
                rows = {}
                async with db.execute(
                    "SELECT id,row_number() OVER (ORDER BY id) FROM warnings WHERE guild = ? and member_id = ?",
                    (guild, member_id),
                ) as cursor:
                    async for entry in cursor:
                        warning_id, pos = entry
                        rows[str(pos)] = warning_id
                async with db.execute(
                    "DELETE FROM warnings WHERE id = ?", (rows[str(number_int)],)
                ):
                    pass
                await db.commit()
                await inter.send(
                    f"Cleared {user.display_name}'s #{number_int} warning.",
                    ephemeral=dpys.EPHEMERAL,
                )
                return True
        except Exception:
            msg = (
                f"{user.display_name} has no warnings."
                if number == "all"
                else f"{user.display_name} does not have that many warnings."
            )
            await inter.send(msg, ephemeral=dpys.EPHEMERAL)
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
        db = dpys.warnings_db
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
        except Exception:
            return
        if warnings_number not in punishments:
            return
        if punishments[warnings_number].duration is not None:
            if punishments[warnings_number].punishment == "temp_ban":
                msg = await warnings._run_before(
                    before, warnings_number, punishments[warnings_number], member
                )
                ban_time = punishments[warnings_number].duration
                try:
                    await member.ban(
                        reason=f"You have received {warnings_number} warning(s)."
                    )
                except (discord.Forbidden, discord.HTTPException) as e:
                    with contextlib.suppress(Exception):
                        await msg.delete()
                    raise e
                ban_time = datetime.datetime.now() + datetime.timedelta(
                    seconds=ban_time
                )
                async with db.execute(
                    "INSERT INTO tempban (guild,member,time) VALUES (?,?,?)",
                    (guild, memberid, ban_time),
                ):
                    pass
                await db.commit()
                return
            if punishments[warnings_number].punishment == "temp_mute":
                add_role_obj = inter.guild.get_role(add_role)
                if not isinstance(add_role_obj, discord.Role):
                    return
                remove_role_obj = inter.guild.get_role(remove_role)
                if add_role_obj in member.roles:
                    return
                mute_time = punishments[warnings_number].duration
                if add_role_obj is not None:
                    await member.add_roles(add_role_obj)
                if remove_role_obj is not None:
                    with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                        await member.remove_roles(remove_role_obj)
                await member.edit(
                    reason=f"You have received {warnings_number} warning(s).",
                    voice_channel=None,
                )
                await mute_on_join.mute_add(inter.guild, member)
                mute_time = datetime.datetime.now() + datetime.timedelta(
                    seconds=mute_time
                )
                async with db.execute(
                    "INSERT INTO tempmute (guild,member,time) VALUES (?,?,?)",
                    (guild, memberid, mute_time),
                ):
                    pass
                await db.commit()
                await warnings._run_before(
                    before, warnings_number, punishments[warnings_number], member
                )
            else:
                timeout_duration = punishments[warnings_number].duration
                await member.timeout(
                    reason=f"You have received {warnings_number} warning(s).",
                    duration=timeout_duration,
                )
                await warnings._run_before(
                    before, warnings_number, punishments[warnings_number], member
                )
                return
        else:
            if punishments[warnings_number].punishment == "ban":
                msg = await warnings._run_before(
                    before, warnings_number, punishments[warnings_number], member
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
                msg = await warnings._run_before(
                    before, warnings_number, punishments[warnings_number], member
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
                add_role_obj = inter.guild.get_role(add_role)
                remove_role_obj = inter.guild.get_role(remove_role)
                if not isinstance(add_role_obj, discord.Role):
                    return
                if remove_role_obj is not None:
                    with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                        await member.remove_roles(remove_role_obj)
                if add_role_obj is not None:
                    await member.add_roles(add_role_obj)
                await member.edit(
                    reason=f"You have received {warnings_number} warning(s).",
                    voice_channel=None,
                )
                await mute_on_join.mute_add(inter.guild, member)
                await warnings._run_before(
                    before, warnings_number, punishments[warnings_number], member
                )

    @staticmethod
    async def temp_mute_loop(
        bot: commands.Bot,
        add_role_func: Callable[[int], Awaitable[Optional[int]]],
        remove_role_func: Optional[Callable[[int], Awaitable[Optional[int]]]] = None,
    ) -> None:
        db = dpys.warnings_db
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
                    mute_time = datetime.datetime.fromisoformat(time_str)
                    role_add = await add_role_func(int(guild_id))
                    role_remove = (
                        None
                        if remove_role_func is None
                        else await remove_role_func(int(guild_id))
                    )
                    if datetime.datetime.now() >= mute_time:
                        with contextlib.suppress(
                            discord.Forbidden, discord.HTTPException, TypeError
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
        db = dpys.warnings_db
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
                    ban_time = datetime.datetime.fromisoformat(time_str)
                    if datetime.datetime.now() >= ban_time:
                        async with db.execute(
                            "DELETE FROM tempban WHERE guild = ? and member = ? and time = ?",
                            (str(guild.id), str(member), time_str),
                        ):
                            pass
                        with contextlib.suppress(
                            discord.Forbidden, discord.HTTPException
                        ):
                            await guild.unban(discord.Object(id=int(member)))
                await db.commit()

    @staticmethod
    async def expire_loop() -> None:
        db = dpys.warnings_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("SELECT id,expires FROM warnings") as cursor:
                async for entry in cursor:
                    warning_id, expires = entry
                    if expires == -1:
                        continue
                    if time.time() >= expires:
                        async with db.execute(
                            "DELETE FROM warnings WHERE id=?", (warning_id,)
                        ):
                            pass
                await db.commit()
