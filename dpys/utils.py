import asyncio
import aiosqlite
import os
import aiohttp

DPYS_DBS = ["warnings.db", "curse.db", "rr.db", "muted.db"]


# utils is not done yet.
# Documentation coming soon.


async def var_can_be_type(var, type, **kwargs) -> bool:
    try:
        type(var)
    except:
        return False
    return True


class GuildData:
    async def curse_set(guild_id: int, dir: str) -> set:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
        curse_set = set()
        async with aiosqlite.connect("curse.db") as db:
            try:
                async with db.execute(
                        "SELECT curse FROM curses WHERE guild = ?", (str(
                            guild_id),)
                ) as cursor:
                    async for entry in cursor:
                        curse_set.add(entry[0])
                return curse_set
            except:
                return set({})

    async def bot_percentage(guild) -> float:
        total = 0
        bot = 0
        for member in guild.members:
            if member.bot:
                bot += 1
            total += 1
        return float(round(bot / total, 2))


class BotData:
    async def bot_percentage(client) -> float:
        total = 0
        bot = 0
        for member in client.get_all_members():
            if member.bot:
                bot += 1
            total += 1
        return float(round(bot / total, 2))

    async def dpys_storage_size(dir: str) -> dict:
        await asyncio.get_event_loop().run_in_executor(None, os.chdir, dir)
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
    async def nitro_code_is_valid(code: str) -> bool:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://discord.com/api/v8/entitlements/gift-codes/{code}"
            ) as r:
                data = await r.json()
        try:
            name = data["store_listing"]["sku"]["name"]
        except:
            return False
        if data["uses"] >= data["max_uses"]:
            return False
        return True
