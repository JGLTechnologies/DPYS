import typing

import disnake as discord
from disnake import ApplicationCommandInteraction

import dpys
from .utils import GuildData


class curse:
    @staticmethod
    async def add_banned_word(inter: ApplicationCommandInteraction, word: str) -> None:
        word = word.lower()
        guildid = str(inter.guild.id)
        db = dpys.curse_db
        async with db.execute(
            """CREATE TABLE if NOT EXISTS curses(
        curse TEXT,
        guild TEXT,
        PRIMARY KEY (curse,guild)
        )"""
        ):
            pass
        await db.commit()
        words = set(word.replace(" ", "").split(","))
        curses = await GuildData.curse_set(inter.guild.id, db)
        for entry in words:
            if entry in curses:
                await inter.send(
                    f"{entry} is already banned.", ephemeral=dpys.EPHEMERAL
                )
                return
        for entry in words:
            async with db.execute(
                "INSERT INTO curses (curse,guild) VALUES (?,?)", (entry, guildid)
            ):
                pass
        await db.commit()
        await inter.send("Those words have been banned.", ephemeral=dpys.EPHEMERAL)

    @staticmethod
    async def remove_banned_word(
        inter: ApplicationCommandInteraction, word: str
    ) -> None:
        db = dpys.curse_db
        guildid = str(inter.guild.id)
        try:
            word = word.lower().replace(" ", "").split(",")
            async with db.execute(
                "SELECT curse FROM curses WHERE guild = ?", (guildid,)
            ) as cursor:
                in_db = False
                async for entry in cursor:
                    curse_word = entry[0]
                    for item in word:
                        if item == curse_word:
                            in_db = True
            if not in_db:
                msg = "Those words are not banned." if len(word) > 1 else "That word is not banned."
                await inter.send(msg, ephemeral=dpys.EPHEMERAL)
                return
            for item in word:
                async with db.execute(
                    "DELETE FROM curses WHERE curse = ? and guild = ?", (item, guildid)
                ):
                    pass
            await db.commit()
            await inter.send(
                "Those words have been unbanned.", ephemeral=dpys.EPHEMERAL
            )
        except Exception:
            await inter.send("Those words are not banned.", ephemeral=dpys.EPHEMERAL)

    @staticmethod
    async def message_filter(
        message: discord.Message, exempt_roles: typing.Optional[typing.List[int]] = None
    ) -> None:
        if (
            message.author.bot
            or message.guild is None
            or message.author.guild_permissions.administrator
        ):
            return
        guildid = str(message.guild.id)
        if exempt_roles is not None:
            for role_id in exempt_roles:
                role = message.guild.get_role(role_id)
                if role is not None and (
                    role in message.author.roles
                    or message.author.top_role.position > role.position
                ):
                    return
        try:
            messagecontent = message.content.lower()
            db = dpys.curse_db
            async with db.execute(
                "SELECT curse FROM curses WHERE guild = ?", (guildid,)
            ) as cursor:
                async for entry in cursor:
                    if entry[0] in messagecontent.split():
                        await message.delete()
                        await message.channel.send(
                            "Do not say that here!", delete_after=5
                        )
        except Exception:
            return

    @staticmethod
    async def message_edit_filter(
        after: discord.Message, exempt_roles: typing.Optional[typing.List[int]] = None
    ) -> None:
        await curse.message_filter(after, exempt_roles)

    @staticmethod
    async def clear_words(inter: ApplicationCommandInteraction) -> None:
        guildid = str(inter.guild.id)
        try:
            db = dpys.curse_db
            async with db.execute("DELETE FROM curses WHERE guild = ?", (guildid,)):
                pass
            await db.commit()
            await inter.send(
                "Unbanned all words from this server.", ephemeral=dpys.EPHEMERAL
            )
        except Exception:
            await inter.send(
                "There are no banned words on this server.",
                ephemeral=dpys.EPHEMERAL,
            )
