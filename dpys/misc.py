import contextlib
import sqlite3
import typing

import disnake as discord
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

import dpys


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
            except Exception:
                continue
        await inter.send(
            f"Successfully reloaded {reloaded}/{total} extensions.",
            ephemeral=dpys.EPHEMERAL,
        )

    @staticmethod
    async def clear_data_on_guild_remove(guild: discord.Guild) -> None:
        warnings_db = dpys.warnings_db
        rr_db = dpys.rr_db
        muted_db = dpys.muted_db
        curse_db = dpys.curse_db

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
            async with rr_db.execute("DELETE FROM rr WHERE guild = ?", (str(guild.id),)):
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
