import asyncio
import sqlite3
import aiosqlite
import os
import aiohttp
import time
from pathlib import Path
from disnake.ext import commands
import disnake

DPYS_DBS = ["warnings.db", "curse.db", "rr.db", "muted.db"]


def get_discord_date(ts: float = None):
    return f"<t:{int(ts or time.time())}> (<t:{int(ts or time.time())}:R>)"


class GuildData:
    @staticmethod
    async def curse_set(guild_id: int, db: aiosqlite.Connection) -> set:
        curse_set = set()
        try:
            async with db.execute(
                    "SELECT curse FROM curses WHERE guild = ?", (str(
                        guild_id),)
            ) as cursor:
                async for entry in cursor:
                    curse_set.add(entry[0])
            return curse_set
        except sqlite3.Error:
            return set()

    @staticmethod
    async def bot_percentage(guild: disnake.Guild) -> float:
        total = 0
        bot = 0
        for member in guild.members:
            if member.bot:
                bot += 1
            total += 1
        return float(round(bot / total, 2))


class BotData:
    @staticmethod
    async def bot_percentage(bot: commands.Bot) -> float:
        total = 0
        bots = 0
        for member in bot.get_all_members():
            if member.bot:
                bots += 1
            total += 1
        return float(round(bots / total, 2))

    @staticmethod
    async def dpys_storage_size(dir: str) -> dict:
        root_directory = Path(dir)
        size = sum(
            f.stat().st_size
            for f in root_directory.glob("**/*")
            if f.is_file() and f.name in DPYS_DBS
        )
        size_kb = size / 1024
        size_mb = size_kb / 1024
        size_gb = size_mb / 1024
        return {
            "size_b": size,
            "size_kb": size_kb,
            "size_mb": size_mb,
            "size_gb": size_gb,
        }


class DiscordUtils:
    @staticmethod
    async def nitro_code_is_valid(code: str) -> bool:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://discord.com/api/v8/entitlements/gift-codes/{code}"
            ) as r:
                data = await r.json()
        try:
            data["store_listing"]["sku"]["name"]
        except KeyError:
            return False
        if data["uses"] >= data["max_uses"]:
            return False
        return True
