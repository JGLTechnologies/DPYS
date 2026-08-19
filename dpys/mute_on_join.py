import contextlib
import sqlite3
import typing

import disnake as discord

import dpys


class mute_on_join:
    @staticmethod
    async def mute_add(guild: discord.Guild, member: discord.Member) -> None:
        guildid = str(guild.id)
        member_id = str(member.id)
        db = dpys.muted_db
        async with db.execute(
            """CREATE TABLE if NOT EXISTS muted(
        name TEXT,
        guild TEXT,
        PRIMARY KEY (name,guild)
        )"""
        ):
            pass
        await db.commit()
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "INSERT INTO muted (name,guild) VALUES (?,?)", (member_id, guildid)
            ):
                pass
            await db.commit()

    @staticmethod
    async def mute_remove(guild: discord.Guild, member: discord.Member) -> None:
        member_id = str(member.id)
        guildid = str(guild.id)
        db = dpys.muted_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "DELETE FROM muted WHERE name = ? and guild = ?", (member_id, guildid)
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
        db = dpys.muted_db
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
        db = dpys.muted_db
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
