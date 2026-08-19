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
from __future__ import annotations

import asyncio
import os
import sqlite3
from pathlib import Path
from typing import Literal, Optional

import aiosqlite
import disnake
import disnake as discord
from disnake.ext import commands

DatabaseName = Literal["warnings", "muted", "rr", "curse"]

COLOR: Optional[discord.Colour] = None
EPHEMERAL = True
warnings_db: Optional[aiosqlite.Connection] = None
muted_db: Optional[aiosqlite.Connection] = None
rr_db: Optional[aiosqlite.Connection] = None
curse_db: Optional[aiosqlite.Connection] = None
_attached_bot: Optional[commands.BotBase] = None
version = "5.6.5"

_SCHEMAS = {
    "warnings": """
                CREATE TABLE IF NOT EXISTS warnings
                (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id TEXT NOT NULL,
                    guild     TEXT NOT NULL,
                    reason    TEXT NOT NULL,
                    expires   REAL NOT NULL DEFAULT -1
                );
                CREATE INDEX IF NOT EXISTS warnings_guild_member
                    ON warnings (guild, member_id);
                CREATE TABLE IF NOT EXISTS tempmute
                (
                    guild            TEXT    NOT NULL,
                    member           TEXT    NOT NULL,
                    time             REAL    NOT NULL,
                    mute_role        TEXT,
                    restore_role     TEXT,
                    had_mute_role    INTEGER NOT NULL DEFAULT 0,
                    had_restore_role INTEGER NOT NULL DEFAULT 1,
                    had_mute_record  INTEGER NOT NULL DEFAULT 0,
                    state            TEXT    NOT NULL DEFAULT 'legacy'
                );
                CREATE TABLE IF NOT EXISTS tempban
                (
                    guild  TEXT NOT NULL,
                    member TEXT NOT NULL,
                    time   REAL NOT NULL,
                    state  TEXT NOT NULL DEFAULT 'legacy'
                );
                UPDATE warnings
                SET expires = -1
                WHERE expires IS NULL;
                UPDATE warnings
                SET expires = -1
                WHERE typeof(expires) NOT IN ('integer', 'real');
                DELETE
                FROM tempmute
                WHERE rowid NOT IN (SELECT MAX(rowid)
                                    FROM tempmute
                                    GROUP BY guild, member);
                DELETE
                FROM tempban
                WHERE rowid NOT IN (SELECT MAX(rowid)
                                    FROM tempban
                                    GROUP BY guild, member);
                CREATE UNIQUE INDEX IF NOT EXISTS tempmute_guild_member
                    ON tempmute (guild, member);
                CREATE UNIQUE INDEX IF NOT EXISTS tempban_guild_member
                    ON tempban (guild, member);
                """,
    "muted": """
             CREATE TABLE IF NOT EXISTS muted
             (
                 name  TEXT NOT NULL,
                 guild TEXT NOT NULL,
                 PRIMARY KEY (name, guild)
             );
             """,
    "rr": """
          CREATE TABLE IF NOT EXISTS rr
          (
              msg_id  TEXT NOT NULL,
              emoji   TEXT NOT NULL,
              role    TEXT NOT NULL,
              guild   TEXT NOT NULL,
              channel TEXT NOT NULL
          );
          CREATE INDEX IF NOT EXISTS rr_guild_message
              ON rr (guild, msg_id);
          CREATE INDEX IF NOT EXISTS rr_guild_channel
              ON rr (guild, channel);
          """,
    "curse": """
             CREATE TABLE IF NOT EXISTS curses
             (
                 curse TEXT NOT NULL,
                 guild TEXT NOT NULL,
                 PRIMARY KEY (curse, guild)
             );
             DELETE
             FROM curses
             WHERE trim(curse) = '';
             """,
}


# noinspection SqlResolve,SqlNoDataSourceInspection
async def _prepare_warnings_schema(connection: aiosqlite.Connection) -> None:
    """Upgrade columns needed before the main idempotent schema script runs."""
    await connection.execute(
        """CREATE TABLE IF NOT EXISTS warnings
           (
               id        INTEGER PRIMARY KEY AUTOINCREMENT,
               member_id TEXT NOT NULL,
               guild     TEXT NOT NULL,
               reason    TEXT NOT NULL,
               expires   REAL NOT NULL DEFAULT -1
           )"""
    )
    async with connection.execute("PRAGMA table_info(warnings)") as cursor:
        warning_columns = {row[1] async for row in cursor}
    if "expires" not in warning_columns:
        await connection.execute(
            "ALTER TABLE warnings ADD COLUMN expires REAL NOT NULL DEFAULT -1"
        )


# noinspection SqlResolve,SqlNoDataSourceInspection
async def _finish_warnings_schema(connection: aiosqlite.Connection) -> None:
    async with connection.execute("PRAGMA table_info(tempmute)") as cursor:
        columns = {row[1] async for row in cursor}
    additions = {
        "mute_role": "ALTER TABLE tempmute ADD COLUMN mute_role TEXT",
        "restore_role": "ALTER TABLE tempmute ADD COLUMN restore_role TEXT",
        "had_mute_role": (
            "ALTER TABLE tempmute ADD COLUMN had_mute_role "
            "INTEGER NOT NULL DEFAULT 0"
        ),
        "had_restore_role": (
            "ALTER TABLE tempmute ADD COLUMN had_restore_role "
            "INTEGER NOT NULL DEFAULT 1"
        ),
        "had_mute_record": (
            "ALTER TABLE tempmute ADD COLUMN had_mute_record "
            "INTEGER NOT NULL DEFAULT 0"
        ),
        "state": (
            "ALTER TABLE tempmute ADD COLUMN state "
            "TEXT NOT NULL DEFAULT 'legacy'"
        ),
    }
    for column, statement in additions.items():
        if column not in columns:
            await connection.execute(statement)
    async with connection.execute("PRAGMA table_info(tempban)") as cursor:
        tempban_columns = {row[1] async for row in cursor}
    if "state" not in tempban_columns:
        await connection.execute(
            "ALTER TABLE tempban ADD COLUMN state TEXT NOT NULL DEFAULT 'legacy'"
        )
    await connection.execute("PRAGMA user_version = 1")


async def _execute_schema(
        connection: aiosqlite.Connection, name: DatabaseName
) -> None:
    """Run one database's idempotent schema migration atomically."""
    await connection.execute("BEGIN IMMEDIATE")
    try:
        if name == "warnings":
            await _prepare_warnings_schema(connection)
        statement = ""
        for line in _SCHEMAS[name].splitlines(keepends=True):
            statement += line
            if sqlite3.complete_statement(statement):
                sql = statement.strip()
                if sql:
                    await connection.execute(sql)
                statement = ""
        if statement.strip():
            await connection.execute(statement)
        if name == "warnings":
            await _finish_warnings_schema(connection)
        await connection.commit()
    except BaseException:
        await asyncio.shield(connection.rollback())
        raise


def display_name(user: discord.Member | discord.User) -> str:
    name = getattr(user, "display_name", None)
    return name if isinstance(name, str) else user.name


def get_database(name: DatabaseName) -> aiosqlite.Connection:
    """Return an initialized DPYS database connection."""
    connections = {
        "warnings": warnings_db,
        "muted": muted_db,
        "rr": rr_db,
        "curse": curse_db,
    }
    connection = connections[name]
    if connection is None:
        raise RuntimeError("dpys.setup() must be awaited before using database helpers")
    return connection


async def close() -> None:
    """Close all DPYS database connections."""
    global warnings_db, muted_db, rr_db, curse_db, _attached_bot
    connections = (warnings_db, muted_db, rr_db, curse_db)
    warnings_db = muted_db = rr_db = curse_db = None
    attached_bot = _attached_bot
    _attached_bot = None
    if attached_bot is not None:
        for attribute, connection in zip(
                ("warnings_db", "muted_db", "rr_db", "curse_db"), connections
        ):
            if getattr(attached_bot, attribute, None) is connection:
                setattr(attached_bot, attribute, None)
    close_operations = [
        connection.close() for connection in connections if connection is not None
    ]
    if not close_operations:
        return
    closing = asyncio.gather(*close_operations, return_exceptions=True)
    try:
        results = await asyncio.shield(closing)
    except asyncio.CancelledError:
        # Shield lets every worker thread close before cancellation is surfaced.
        await closing
        raise
    for result in results:
        if isinstance(result, Exception):
            raise result


async def setup(
        bot: commands.BotBase,
        dir: str | os.PathLike[str],
        color: disnake.colour.Colour = discord.Colour.blurple(),
) -> None:
    """Initialize DPYS storage and attach its connections to ``bot``."""
    global warnings_db, muted_db, rr_db, curse_db, COLOR, _attached_bot

    await close()
    directory = Path(dir)
    directory.mkdir(parents=True, exist_ok=True)

    opened: dict[DatabaseName, aiosqlite.Connection] = {}
    try:
        for name in ("warnings", "muted", "rr", "curse"):
            connection = await aiosqlite.connect(directory / f"{name}.db")
            opened[name] = connection
            await _execute_schema(connection, name)
    except BaseException:
        for connection in opened.values():
            try:
                await asyncio.shield(connection.close())
            except BaseException:
                pass
        raise

    warnings_db = opened["warnings"]
    muted_db = opened["muted"]
    rr_db = opened["rr"]
    curse_db = opened["curse"]
    COLOR = color
    bot.warnings_db = warnings_db
    bot.muted_db = muted_db
    bot.rr_db = rr_db
    bot.curse_db = curse_db
    _attached_bot = bot


# Import public helpers after shared package state has been initialized.
from .admin import admin
from .curse import curse
from .misc import misc
from .mute_on_join import mute_on_join
from .rr import rr
from .utils import BotData, DiscordUtils, GuildData
from .warnings import warnings
