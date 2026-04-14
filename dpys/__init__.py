# This library is in development and bugs can be expected. If you encounter any bugs, want to give feedback, or would like to contribute, join our Discord server.
# https://jgltechnologies.com/dicord

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
import os

import aiosqlite
import disnake
import disnake as discord
from disnake.ext import commands

from .admin import admin
from .curse import curse
from .misc import misc
from .mute_on_join import mute_on_join
from .rr import rr
from .utils import BotData, DiscordUtils, GuildData
from .warnings import warnings

COLOR = None
EPHEMERAL = True
warnings_db: aiosqlite.Connection | None = None
muted_db: aiosqlite.Connection | None = None
rr_db: aiosqlite.Connection | None = None
curse_db: aiosqlite.Connection | None = None
version = "5.6.5"


def display_name(user: discord.Member | discord.User) -> str:
    return getattr(user, "display_name", user.name)


async def setup(
    bot: commands.BotBase,
    dir: str,
    color: disnake.colour.Colour = discord.Colour.blurple(),
):
    global warnings_db, muted_db, rr_db, curse_db, COLOR
    warnings_db = await aiosqlite.connect(os.path.join(dir, "warnings.db"))
    muted_db = await aiosqlite.connect(os.path.join(dir, "muted.db"))
    rr_db = await aiosqlite.connect(os.path.join(dir, "rr.db"))
    curse_db = await aiosqlite.connect(os.path.join(dir, "curse.db"))
    COLOR = color
    bot.warnings_db = warnings_db
    bot.muted_db = muted_db
    bot.rr_db = rr_db
    bot.curse_db = curse_db

print(
    "We recommend that you read https://jgltechnologies.com/dpys before you use DPYS."
)
