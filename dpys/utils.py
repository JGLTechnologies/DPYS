import asyncio
import inspect
import math
import time
from pathlib import Path
from urllib.parse import quote

import aiosqlite
import aiohttp
import disnake
from disnake.ext import commands

DPYS_DBS = ["warnings.db", "curse.db", "rr.db", "muted.db"]

list_scrollers: dict[int, list["ListScroller"]] = {}


class ListScroller(disnake.ui.View):
    member_id: int
    command_name: str

    def __init__(
            self,
            count: int,
            array: list,
            func,
            inter: disnake.ApplicationCommandInteraction,
            timeout: int = 120,
    ):
        if count <= 0:
            raise ValueError("count must be greater than zero")
        if inter.guild is None or inter.application_command is None:
            raise ValueError("ListScroller requires a guild application command")

        guild_scrollers = list_scrollers.setdefault(inter.guild.id, [])
        for ls in guild_scrollers[:]:
            if ls.member_id == inter.author.id and ls.command_name == inter.application_command.name:
                ls.clear_items()
                ls.stop()
                ls.clear_data()
        super().__init__(timeout=timeout)
        self.pages = math.ceil(len(array) / count)
        self.count = count
        self.guild_id = inter.guild.id
        self.command_name = inter.application_command.name
        self.member_id = inter.author.id
        self.list = array
        self.func = func
        self.pos = 0
        self.navigation_lock = asyncio.Lock()
        self.next = Next(
            label="Next",
            style=disnake.ButtonStyle.secondary,
            custom_id=f"next{id(self)}",
        )
        self.prev = Prev(
            label="Prev",
            style=disnake.ButtonStyle.secondary,
            custom_id=f"prev{id(self)}",
        )
        guild_scrollers.append(self)

    async def render_page(self):
        start = self.pos * self.count
        result = self.func(
            self.list[start: start + self.count],
            start + 1,
            (self.pos + 1, self.pages),
        )
        if inspect.isawaitable(result):
            return await result
        return result

    async def reset(self):
        self.pages = math.ceil(len(self.list) / self.count)
        self.pos = min(self.pos, max(self.pages - 1, 0))
        self.clear_items()
        self.next.disabled = self.pos >= self.pages - 1
        self.prev.disabled = self.pos == 0
        self.add_item(self.prev)
        self.add_item(self.next)

    async def start(self):
        await self.reset()

    async def interaction_check(
            self, interaction: disnake.MessageInteraction
    ) -> bool:
        if interaction.author.id == self.member_id:
            return True
        await interaction.response.send_message(
            "Only the user who opened this view can control it.", ephemeral=True
        )
        return False

    def clear_data(self):
        guild_scrollers = list_scrollers.get(self.guild_id)
        if guild_scrollers is None:
            return
        if self in guild_scrollers:
            guild_scrollers.remove(self)
        if not guild_scrollers:
            list_scrollers.pop(self.guild_id, None)

    async def on_timeout(self) -> None:
        self.clear_data()


class Next(disnake.ui.Button):
    async def callback(self, inter: disnake.MessageInteraction):
        if self.view.navigation_lock.locked() or self.view.pos >= self.view.pages - 1:
            await inter.response.defer()
            return
        async with self.view.navigation_lock:
            self.view.pos += 1
            self.view.prev.disabled = False
            self.disabled = self.view.pos >= self.view.pages - 1
            embed = await self.view.render_page()
            await inter.response.edit_message(embed=embed, view=self.view)


class Prev(disnake.ui.Button):
    async def callback(self, inter: disnake.MessageInteraction):
        if self.view.navigation_lock.locked() or self.view.pos <= 0:
            await inter.response.defer()
            return
        async with self.view.navigation_lock:
            self.view.pos -= 1
            self.view.next.disabled = False
            self.disabled = self.view.pos == 0
            embed = await self.view.render_page()
            await inter.response.edit_message(embed=embed, view=self.view)


def get_discord_date(ts: float | int | None = None) -> str:
    timestamp = time.time() if ts is None else ts
    return f"<t:{int(timestamp)}> (<t:{int(timestamp)}:R>)"


class GuildData:
    @staticmethod
    async def curse_set(guild_id: int, db: aiosqlite.Connection) -> set[str]:
        curse_set: set[str] = set()
        # noinspection SqlResolve,SqlNoDataSourceInspection
        async with db.execute(
                "SELECT curse FROM curses WHERE guild = ?", (str(guild_id),)
        ) as cursor:
            async for entry in cursor:
                if entry[0]:
                    curse_set.add(entry[0])
        return curse_set

    @staticmethod
    async def bot_percentage(guild: disnake.Guild) -> float:
        total = len(guild.members)
        if total == 0:
            return 0.0
        bots = sum(member.bot for member in guild.members)
        return round(bots / total, 2)


class BotData:
    @staticmethod
    async def bot_percentage(bot: commands.Bot) -> float:
        members = list(bot.get_all_members())
        if not members:
            return 0.0
        bots = sum(member.bot for member in members)
        return round(bots / len(members), 2)

    @staticmethod
    async def dpys_storage_size(dir: str) -> dict[str, int | float]:
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
        code = code.strip()
        if not code:
            return False

        timeout = aiohttp.ClientTimeout(total=10)
        url = f"https://discord.com/api/v10/entitlements/gift-codes/{quote(code, safe='')}"
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return False
                    try:
                        data = await response.json(content_type=None)
                    except (aiohttp.ContentTypeError, ValueError):
                        return False
        except (aiohttp.ClientError, TimeoutError):
            return False

        if not isinstance(data, dict):
            return False

        store_listing = data.get("store_listing")
        uses = data.get("uses")
        max_uses = data.get("max_uses")
        if not isinstance(store_listing, dict):
            return False
        if not isinstance(uses, int) or not isinstance(max_uses, int):
            return False
        return uses < max_uses
