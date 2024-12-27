import asyncio
import sqlite3
import aiosqlite
import aiohttp
import time
from pathlib import Path
from disnake.ext import commands
import disnake
import math

DPYS_DBS = ["warnings.db", "curse.db", "rr.db", "muted.db"]


list_scrollers = {}


class ListScroller(disnake.ui.View):
    def __init__(self, count: int, array: list, func, inter: disnake.ApplicationCommandInteraction, timeout: int = 120):
        global list_scrollers
        if list_scrollers.get(inter.guild.id) is None:
            list_scrollers[inter.guild.id] = []
        guild_list_scrollers = list_scrollers.get(inter.guild.id)
        for i, ls in enumerate(guild_list_scrollers):
            if ls.member_id ==inter.author.id and ls.command_name == inter.application_command.name:
                ls.stop()
                guild_list_scrollers.pop(i)
        list_scrollers[inter.guild.id].append(self)
        super().__init__(timeout=timeout)
        self.pages = math.ceil(len(array)/count)
        self.count = count
        self.guild_id = inter.guild.id
        self.command_name = inter.application_command.name
        self.member_id = inter.author.id
        self.list = array
        self.func = func
        self.pos = 0
        self.next_lock = asyncio.Semaphore(1)
        self.prev_lock = asyncio.Semaphore(1)
        self.next = Next(label="Next", style=disnake.ButtonStyle.grey, custom_id="next")
        self.prev = Prev(label="Prev", style=disnake.ButtonStyle.grey, custom_id="prev")

    async def start(self):
        if len(self.list) > self.count:
            self.prev.disabled = True
            self.add_item(self.prev)
            self.add_item(self.next)

    def on_timeout(self) -> None:
        guild_list_scrollers = list_scrollers[self.guild_id]
        for i, ls in enumerate(guild_list_scrollers):
            if ls == self:
                guild_list_scrollers.pop(i)



class Next(disnake.ui.Button):
    async def callback(self, inter: disnake.MessageInteraction):
        if self.view.next_lock.locked():
            return
        async with self.view.next_lock:
            self.view.pos+=1
            self.view.prev.disabled = False
            if len(self.view.list)-((self.view.pos+1)*self.view.count) <= 0:
                self.disabled = True
            embed = self.view.func(self.view.list[self.view.pos*self.view.count:self.view.pos*self.view.count+self.view.count], self.view.pos*self.view.count+1, (self.view.pos+1, self.view.pages))
            await inter.response.edit_message(embed=embed, view=self.view)

class Prev(disnake.ui.Button):
    async def callback(self, inter: disnake.MessageInteraction):
        if self.view.prev_lock.locked():
            return
        async with self.view.prev_lock:
            self.view.pos -= 1
            self.view.next.disabled = False
            if self.view.pos == 0:
                self.disabled = True
            embed = self.view.func(self.view.list[self.view.pos*self.view.count:self.view.pos*self.view.count+self.view.count], self.view.pos*self.view.count+1, (self.view.pos+1, self.view.pages))
            await inter.response.edit_message(embed=embed, view=self.view)


def get_discord_date(ts: float = None):
    return f"<t:{int(ts or time.time())}> (<t:{int(ts or time.time())}:R>)"


class GuildData:
    @staticmethod
    async def curse_set(guild_id: int, db: aiosqlite.Connection) -> set:
        curse_set = set()
        try:
            async with db.execute(
                "SELECT curse FROM curses WHERE guild = ?", (str(guild_id),)
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
