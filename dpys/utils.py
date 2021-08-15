import asyncio
import json
import aiosqlite
import os
import aiohttp

from discord.ext import commands
from pathlib import Path
from aiohttp import web

DPYS_DBS = ["warnings.db", "curse.db", "rr.db", "muted.db"]

# utils is not done yet.

async def var_can_be_type(var, type, **kwargs) -> bool:
    try:
        type(var)
    except:
        return False
    return True

class GuildData:

    async def curse_set(guild_id : int, dir : str) -> set:
        os.chdir(dir)
        curse_set = set()
        async with aiosqlite.connect("curse.db") as db:
            try:
                async with db.execute("SELECT curse FROM curses WHERE guild = ?", (str(guild_id),)) as cursor:
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
        return float(round(bot/total, 2))
        

class BotData:

    async def bot_percentage(client) -> float:
        total = 0
        bot = 0
        for member in client.get_all_members():
            if member.bot:
                bot += 1
            total += 1
        return float(round(bot/total, 2))

    async def dpys_storage_size(dir : str) -> dict:
        os.chdir(dir)
        root_directory = Path(dir)
        size = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file() and f.name in DPYS_DBS)
        size_kb = size/1024
        size_mb = size_kb/1024
        size_gb = size_mb/1024
        return {"size_b":size, "size_kb":size_kb, "size_mb":size_mb, "size_gb":size_gb}

class DiscordUtils:

    async def nitro_code_is_valid(code : str) -> bool:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://discord.com/api/v8/entitlements/gift-codes/{code}") as r:
                data = await r.json()
        try:
            name = data["store_listing"]["sku"]["name"]
        except:
            return False
        if data["uses"] >= data["max_uses"]:
            return False
        return True

# class DPYSApi:

#     def __init__(self, dir : str, port : int, api_keys : list[str], bot, **kwargs):
#         self.bot = bot
#         self.keys = set(api_keys)
#         self.dir = dir
#         self.port = port
#         self._loop = asyncio.new_event_loop()

#     routes = web.RouteTableDef()

#     @property
#     def loop(self):
#         return self._loop

#     @routes.post("/add_curse")
#     async def add_curse(self, request) -> web.Response:
#         os.chdir(self.dir)
#         data = await request.post()
#         if request.headers.get("api-key") not in self.keys:
#             return web.Response(text=json.dumps({"error-codes":"Inavlid api-key", "success":False}), status=401)
#         if data.get("guild") is None:
#             return web.Response(text=json.dumps({"error-codes":"Missing input guild", "success":False}), status=401)
#         if data.get("curse") is None:
#             return web.Response(text=json.dumps({"error-codes":"Missing input curse", "success":False}), status=401)
#         if self.bot.get_guild(int(data["guild"])) is None:
#             return web.Response(text=json.dumps({"error-codes":"Invalid guild", "success":False}), status=406)
#         async with aiosqlite.connect("curses.db") as db:
#             await db.execute(f"""CREATE TABLE if NOT EXISTS curses(
#             curse TEXT,
#             guild TEXT,
#             PRIMARY KEY (curse,guild)
#             )""")
#             await db.commit()
#             try:
#                 await db.execute("INSERT INTO curses (curse,guild) VALUES (?,?)", (str(data["curse"]), str(data["guild"])))
#                 await db.commit()
#                 return web.Response(text=json.dumps({"success":True}), status=200)
#             except:
#                 return web.Response(text=json.dumps({"error-codes":"Curse already in list", "success":False}), status=406)

#     @routes.post("/remove_curse")
#     async def remove_curse(self, request) -> web.Response:
#         os.chdir(self.dir)
#         data = await request.post()
#         if request.headers.get("api-key") not in self.keys:
#             return web.Response(text=json.dumps({"error-codes":"Inavlid api-key", "success":False}), status=401)
#         if data.get("guild") is None:
#             return web.Response(text=json.dumps({"error-codes":"Missing input guild", "success":False}), status=401)
#         if data.get("curse") is None:
#             return web.Response(text=json.dumps({"error-codes":"Missing input curse", "success":False}), status=401)
#         if self.bot.get_guild(int(data["guild"])) is None:
#             return web.Response(text=json.dumps({"error-codes":"Invalid guild", "success":False}), status=406)
#         async with aiosqlite.connect("curses.db") as db:
#             await db.execute(f"""CREATE TABLE if NOT EXISTS curses(
#             curse TEXT,
#             guild TEXT,
#             PRIMARY KEY (curse,guild)
#             )""")
#             await db.commit()
#             if str(data["curse"]) not in GuildData.curse_set():
#                 return web.Response(text=json.dumps({"error-codes":"Curse not in list", "success":False}), status=404)
#             await db.execute("DELETE FROM curses WHERE curse = ? and guild = ?", (str(data["curse"]), str(data["guild"])))
#             await db.commit()
#             return web.Response(text=json.dumps({"success":True}), status=200)

#     async def run_api(self) -> None:
#         app = web.Application()
#         app.add_routes(self.routes)
#         runner = web.AppRunner(app)
#         await runner.setup()
#         site = web.TCPSite(runner, port=self.port)
#         await site.start()

