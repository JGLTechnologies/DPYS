import asyncio
import contextlib
import sqlite3

import disnake
import disnake as discord
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

import dpys
from .utils import ListScroller


class rr:
    @staticmethod
    async def command(
        inter: ApplicationCommandInteraction,
        emoji: str,
        role: str,
        title: str,
        description: str,
    ) -> None:
        db = dpys.rr_db
        await inter.send(
            "Attempting to create reaction role...", ephemeral=dpys.EPHEMERAL
        )
        async with db.execute(
            """CREATE TABLE IF NOT EXISTS rr(
        msg_id TEXT,
        emoji UNICODE,
        role TEXT,
        guild TEXT,
        channel TEXT
        )"""
        ):
            pass
        await db.commit()
        embed = discord.Embed(
            title=title, color=dpys.COLOR, description=description
        )
        role = role.replace("<", "").replace(">", "").replace("@", "").replace("&", "")
        emoji = emoji.replace(" ", "")
        emoji_list = emoji.split(",")
        try:
            role_list = [inter.guild.get_role(int(r)) for r in role.split(",")]
        except Exception:
            await inter.followup.send("Invalid role", ephemeral=dpys.EPHEMERAL)
            return
        if len(role_list) != len(emoji_list):
            await inter.followup.send(
                "Emoji list must be same length as role list.",
                ephemeral=dpys.EPHEMERAL,
            )
            return
        if len(emoji_list) > 1:
            for role_obj in role_list:
                if role_obj is None:
                    await inter.followup.send(
                        "Invalid roles", ephemeral=dpys.EPHEMERAL
                    )
                    return
            msg = await inter.channel.send(embed=embed)
            for index, emoji_value in enumerate(emoji_list):
                role_obj = role_list[index]
                try:
                    await msg.add_reaction(emoji_value)
                except discord.HTTPException:
                    await inter.followup.send(
                        "Invalid emojis", ephemeral=dpys.EPHEMERAL
                    )
                    await msg.delete()
                    return
                async with db.execute(
                    "INSERT INTO rr (msg_id,emoji,role,guild,channel) VALUES (?,?,?,?,?)",
                    (
                        str(msg.id),
                        emoji_value,
                        str(role_obj.id),
                        str(inter.guild.id),
                        str(inter.channel.id),
                    ),
                ):
                    pass
            await inter.followup.send(
                "Successfully created the reaction role.",
                ephemeral=dpys.EPHEMERAL,
            )
            await db.commit()
            return

        role_obj = role_list[0]
        if role_obj is None:
            await inter.followup.send("Invalid role", ephemeral=dpys.EPHEMERAL)
            return
        msg = await inter.channel.send(embed=embed)
        try:
            await msg.add_reaction(emoji)
        except discord.HTTPException:
            await inter.followup.send("Invalid emojis", ephemeral=dpys.EPHEMERAL)
            await msg.delete()
            return
        async with db.execute(
            "INSERT INTO rr (msg_id,emoji,role,guild,channel) VALUES (?,?,?,?,?)",
            (
                str(msg.id),
                emoji,
                str(role_obj.id),
                str(inter.guild.id),
                str(inter.channel.id),
            ),
        ):
            pass
        await db.commit()
        await inter.followup.send(
            "Successfully created the reaction role.", ephemeral=dpys.EPHEMERAL
        )

    @staticmethod
    async def add(payload: discord.RawReactionActionEvent, bot: commands.Bot) -> None:
        if payload.guild_id is None or payload.member.bot:
            return
        db = dpys.rr_db
        guild = bot.get_guild(payload.guild_id)
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT emoji,role FROM rr WHERE guild = ? and msg_id = ?",
                (str(guild.id), str(payload.message_id)),
            ) as cursor:
                async for entry in cursor:
                    emoji, role = entry
                    role = guild.get_role(int(role))
                    if str(payload.emoji) == emoji:
                        with contextlib.suppress(
                            discord.Forbidden, discord.HTTPException
                        ):
                            await payload.member.add_roles(role)

    @staticmethod
    async def remove(
        payload: discord.RawReactionActionEvent, bot: commands.Bot
    ) -> None:
        if payload.guild_id is None:
            return
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member.bot:
            return
        db = dpys.rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT emoji,role FROM rr WHERE guild = ? and msg_id = ?",
                (str(guild.id), str(payload.message_id)),
            ) as cursor:
                async for entry in cursor:
                    emoji, role = entry
                    role = guild.get_role(int(role))
                    if str(payload.emoji) == emoji:
                        with contextlib.suppress(
                            discord.Forbidden, discord.HTTPException
                        ):
                            await member.remove_roles(role)

    @staticmethod
    async def clear_all(inter: ApplicationCommandInteraction) -> None:
        guild = str(inter.guild.id)
        db = dpys.rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute("DELETE FROM rr WHERE guild = ?", (guild,)):
                pass
            await db.commit()
        await inter.send(
            "Deleted all reaction role info for this server.",
            ephemeral=dpys.EPHEMERAL,
        )

    @staticmethod
    async def clear_one(
        inter: ApplicationCommandInteraction, message_id: int | str
    ) -> None:
        guild = str(inter.guild.id)
        message_ids = str(message_id).replace(" ", "").split(",")
        db = dpys.rr_db
        for entry in message_ids:
            try:
                async with db.execute(
                    "DELETE FROM rr WHERE guild = ? and msg_id = ?", (guild, entry)
                ):
                    pass
            except Exception:
                break
        await db.commit()
        await inter.send(
            f"Deleted all reaction role info with message ID(s): {', '.join(message_ids)}",
            ephemeral=dpys.EPHEMERAL,
        )

    @staticmethod
    async def clear_on_message_delete(message: discord.Message) -> None:
        if message.guild is None:
            return
        db = dpys.rr_db
        guild = str(message.guild.id)
        message_id = str(message.id)
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT msg_id FROM rr WHERE guild = ?", (guild,)
            ) as cursor:
                async for entry in cursor:
                    if entry[0] == message_id:
                        async with db.execute(
                            "DELETE FROM rr WHERE msg_id = ? and guild = ?",
                            (message_id, guild),
                        ):
                            pass
                        break
                await db.commit()

    @staticmethod
    async def clear_on_channel_delete(channel: discord.TextChannel) -> None:
        channel_id = channel.id
        guild = channel.guild.id
        db = dpys.rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT channel FROM rr WHERE guild = ?", (str(guild),)
            ) as cursor:
                async for entry in cursor:
                    db_channel = int(entry[0])
                    if db_channel == channel_id:
                        async with db.execute(
                            "DELETE FROM rr WHERE guild = ? and channel = ?",
                            (str(guild), str(db_channel)),
                        ):
                            pass
                        break
                await db.commit()

    @staticmethod
    async def clear_on_thread_delete(thread: discord.Thread) -> None:
        thread_id = thread.id
        guild = thread.guild.id
        db = dpys.rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT channel FROM rr WHERE guild = ?", (str(guild),)
            ) as cursor:
                async for entry in cursor:
                    db_channel = int(entry[0])
                    if db_channel == thread_id:
                        async with db.execute(
                            "DELETE FROM rr WHERE guild = ? and channel = ?",
                            (str(guild), str(db_channel)),
                        ):
                            pass
                        break
                await db.commit()

    @staticmethod
    async def clear_on_bulk_message_delete(
        payload: discord.RawBulkMessageDeleteEvent,
    ) -> None:
        ids = payload.message_ids
        guild = payload.guild_id
        if guild is None:
            return
        db = dpys.rr_db
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT msg_id FROM rr WHERE guild = ?", (str(guild),)
            ) as cursor:
                async for entry in cursor:
                    msg_id = int(entry[0])
                    if msg_id in ids:
                        async with db.execute(
                            "DELETE FROM rr WHERE guild = ? and msg_id = ?",
                            (str(guild), str(msg_id)),
                        ):
                            pass
            await db.commit()

    class Delete(disnake.ui.Button):
        async def callback(self, inter: discord.MessageInteraction) -> None:
            if self.view.delete_lock.locked():
                return
            async with self.view.delete_lock:
                current = self.view.list[
                    self.view.pos * self.view.count : self.view.pos * self.view.count
                    + self.view.count
                ][0]
                msg_id = current[2]
                channel = current[3]
                self.view.list.pop(self.view.pos)
                await self.view.reset()
                try:
                    async with dpys.rr_db.execute(
                        "DELETE FROM rr WHERE guild = ? and msg_id = ?",
                        (str(inter.guild.id), str(msg_id)),
                    ):
                        pass
                except Exception:
                    pass
                with contextlib.suppress(Exception):
                    msg = await channel.fetch_message(msg_id)
                    await msg.delete()
                await dpys.rr_db.commit()
                if len(self.view.list) == 0:
                    self.view.clear_items()
                    self.view.stop()
                    await inter.response.edit_message(
                        "There are no reaction roles in this server.",
                        view=self.view,
                        embed=None,
                    )
                    self.view.clear_data()
                    return
                await self.view.reset()
                self.view.add_item(self)
                embed = self.view.func(
                    self.view.list[
                        self.view.pos * self.view.count : self.view.pos * self.view.count
                        + self.view.count
                    ],
                    self.view.pos * self.view.count + 1,
                    (self.view.pos + 1, self.view.pages),
                )
                await inter.response.edit_message(embed=embed, view=self.view)

    @staticmethod
    async def display(inter: ApplicationCommandInteraction) -> None:
        guild = str(inter.guild.id)
        db = dpys.rr_db
        reaction_roles = []
        with contextlib.suppress(sqlite3.Error):
            async with db.execute(
                "SELECT msg_id FROM rr WHERE guild = ? GROUP BY msg_id", (guild,)
            ) as cursor:
                async for entry in cursor:
                    async with db.execute(
                        "SELECT role,emoji,channel,msg_id FROM rr WHERE guild = ? and msg_id = ?",
                        (guild, entry[0]),
                    ) as result:
                        roles = []
                        emojis = []
                        channel_id = None
                        msg_id = int(entry[0])
                        async for row in result:
                            role_id, emoji, channel_id, msg_id = row
                            roles.append(inter.guild.get_role(int(role_id)))
                            emojis.append(emoji)
                        channel = inter.guild.get_channel(int(channel_id))
                        reaction_roles.append((roles, emojis, msg_id, channel))
            if len(reaction_roles) > 0:
                def func(array, _, page_info):
                    embed = disnake.Embed(title="Reaction Roles", color=dpys.COLOR)
                    embed.add_field(
                        name="Roles",
                        value=" ".join(
                            [
                                f"{role.mention if role is not None else '@deleted-role'}"
                                for role in array[0][0]
                            ]
                        ),
                        inline=False,
                    )
                    embed.add_field(
                        name="Emojis",
                        value=" ".join(array[0][1]),
                        inline=False,
                    )
                    embed.add_field(
                        name="Channel",
                        value=f"{array[0][3].mention if array[0][3] is not None else '#deleted-channel'}",
                        inline=False,
                    )
                    embed.add_field(name="Message ID", value=array[0][2], inline=False)
                    embed.set_footer(text=f"Page {page_info[0]}/{page_info[1]}")
                    return embed

                view = ListScroller(1, reaction_roles, func, inter)
                embed = func(reaction_roles[0:1], 1, (1, len(reaction_roles)))
                delete_button = rr.Delete(
                    label="Delete",
                    style=disnake.ButtonStyle.red,
                    custom_id=f"delete{id(view)}",
                )
                view.delete_lock = asyncio.Semaphore(1)
                await view.start()
                view.add_item(delete_button)
                await inter.send(
                    embed=embed, view=view, ephemeral=dpys.EPHEMERAL
                )
                return
        await inter.send(
            "There are no reaction roles in this server.", ephemeral=dpys.EPHEMERAL
        )
