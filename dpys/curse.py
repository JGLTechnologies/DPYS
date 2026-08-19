import re

import disnake as discord
from disnake import ApplicationCommandInteraction

import dpys
from .utils import GuildData


def _parse_words(value: str) -> set[str]:
    return {
        re.sub(r"\s+", " ", entry.strip().casefold())
        for entry in value.split(",")
        if entry.strip()
    }


def _contains_banned_word(content: str, banned_words: set[str]) -> bool:
    normalized = re.sub(r"\s+", " ", content.casefold())
    return any(
        re.search(rf"(?<!\w){re.escape(word)}(?!\w)", normalized)
        for word in banned_words
        if word
    )


# noinspection PyPep8Naming,SqlResolve,SqlNoDataSourceInspection
class curse:
    @staticmethod
    async def add_banned_word(inter: ApplicationCommandInteraction, word: str) -> None:
        if inter.guild is None:
            raise ValueError("This helper can only be used in a guild")
        guildid = str(inter.guild.id)
        db = dpys.get_database("curse")
        words = _parse_words(word)
        if not words:
            await inter.send("Provide at least one word.", ephemeral=dpys.EPHEMERAL)
            return
        curses = await GuildData.curse_set(inter.guild.id, db)
        new_words = words - curses
        if not new_words:
            message = "Those words are already banned." if len(words) > 1 else "That word is already banned."
            await inter.send(message, ephemeral=dpys.EPHEMERAL)
            return
        await db.executemany(
            "INSERT OR IGNORE INTO curses (curse,guild) VALUES (?,?)",
            [(entry, guildid) for entry in sorted(new_words)],
        )
        await db.commit()
        message = "Those words have been banned." if len(new_words) > 1 else "That word has been banned."
        await inter.send(message, ephemeral=dpys.EPHEMERAL)

    @staticmethod
    async def remove_banned_word(
            inter: ApplicationCommandInteraction, word: str
    ) -> None:
        if inter.guild is None:
            raise ValueError("This helper can only be used in a guild")
        db = dpys.get_database("curse")
        guildid = str(inter.guild.id)
        words = _parse_words(word)
        if not words:
            await inter.send("Provide at least one word.", ephemeral=dpys.EPHEMERAL)
            return
        existing = await GuildData.curse_set(inter.guild.id, db)
        removable = words & existing
        if not removable:
            message = "Those words are not banned." if len(words) > 1 else "That word is not banned."
            await inter.send(message, ephemeral=dpys.EPHEMERAL)
            return
        await db.executemany(
            "DELETE FROM curses WHERE curse = ? and guild = ?",
            [(entry, guildid) for entry in sorted(removable)],
        )
        await db.commit()
        message = "Those words have been unbanned." if len(removable) > 1 else "That word has been unbanned."
        await inter.send(message, ephemeral=dpys.EPHEMERAL)

    @staticmethod
    async def message_filter(
            message: discord.Message, exempt_roles: list[int] | None = None
    ) -> None:
        if (
                message.author.bot
                or message.guild is None
                or not isinstance(message.author, discord.Member)
                or message.author.guild_permissions.administrator
        ):
            return
        if exempt_roles is not None:
            for role_id in exempt_roles:
                role = message.guild.get_role(role_id)
                if role is not None and role in message.author.roles:
                    return
        db = dpys.get_database("curse")
        banned_words = await GuildData.curse_set(message.guild.id, db)
        if not _contains_banned_word(message.content, banned_words):
            return
        try:
            await message.delete()
            await message.channel.send("Do not say that here!", delete_after=5)
        except (discord.Forbidden, discord.HTTPException):
            return

    @staticmethod
    async def message_edit_filter(
            after: discord.Message, exempt_roles: list[int] | None = None
    ) -> None:
        await curse.message_filter(after, exempt_roles)

    @staticmethod
    async def clear_words(inter: ApplicationCommandInteraction) -> None:
        if inter.guild is None:
            raise ValueError("This helper can only be used in a guild")
        guildid = str(inter.guild.id)
        db = dpys.get_database("curse")
        async with db.execute(
                "DELETE FROM curses WHERE guild = ?", (guildid,)
        ) as cursor:
            deleted = cursor.rowcount
        await db.commit()
        message = (
            "Unbanned all words from this server."
            if deleted
            else "There are no banned words on this server."
        )
        await inter.send(message, ephemeral=dpys.EPHEMERAL)
