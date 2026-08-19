import disnake as discord
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

import dpys


# noinspection PyPep8Naming,SqlResolve,SqlNoDataSourceInspection
class misc:
    @staticmethod
    async def reload(
            inter: ApplicationCommandInteraction, bot: commands.BotBase, cogs: list[str]
    ) -> None:
        if not isinstance(cogs, list) or not all(
                isinstance(cog, str) for cog in cogs
        ):
            raise TypeError("cogs must be a list of extension names")
        deferred = False
        if not inter.response.is_done():
            await inter.response.defer(ephemeral=dpys.EPHEMERAL)
            deferred = True
        total = len(cogs)
        failed: list[str] = []
        for cog in cogs:
            try:
                bot.reload_extension(cog)
            except commands.ExtensionError:
                failed.append(cog)
        reloaded = total - len(failed)
        message = f"Successfully reloaded {reloaded}/{total} extensions."
        if failed:
            message += f" Failed: {', '.join(failed)}."
        if deferred:
            await inter.edit_original_response(content=message)
        else:
            await inter.send(message, ephemeral=dpys.EPHEMERAL)

    @staticmethod
    async def clear_data_on_guild_remove(guild: discord.Guild) -> None:
        guild_id = str(guild.id)
        operations = (
            (
                dpys.get_database("warnings"),
                (
                    "DELETE FROM tempmute WHERE guild = ?",
                    "DELETE FROM tempban WHERE guild = ?",
                    "DELETE FROM warnings WHERE guild = ?",
                ),
            ),
            (dpys.get_database("rr"), ("DELETE FROM rr WHERE guild = ?",)),
            (dpys.get_database("muted"), ("DELETE FROM muted WHERE guild = ?",)),
            (dpys.get_database("curse"), ("DELETE FROM curses WHERE guild = ?",)),
        )
        first_error: Exception | None = None
        for database, queries in operations:
            try:
                for query in queries:
                    async with database.execute(query, (guild_id,)):
                        pass
                await database.commit()
            except Exception as error:
                await database.rollback()
                first_error = first_error or error
        if first_error is not None:
            raise first_error
