import contextlib
import sqlite3

import disnake
import disnake as discord
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

import dpys
from .utils import ListScroller


def _guild(inter: ApplicationCommandInteraction) -> discord.Guild:
    if inter.guild is None:
        raise ValueError("This helper can only be used in a guild")
    return inter.guild


async def _resolve_member(
        guild: discord.Guild,
        user_id: int,
        payload_member: discord.Member | None = None,
) -> discord.Member | None:
    member = payload_member or guild.get_member(user_id)
    if member is not None:
        return member
    try:
        return await guild.fetch_member(user_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


def _emoji_key(emoji: discord.PartialEmoji) -> tuple[str, int | str | None]:
    """Return a stable identity: custom emoji ID or Unicode value."""
    if emoji.id is not None:
        return "custom", emoji.id
    return "unicode", emoji.name


def _emoji_matches(stored: str, payload_emoji: discord.PartialEmoji) -> bool:
    return _emoji_key(discord.PartialEmoji.from_str(stored)) == _emoji_key(
        payload_emoji
    )


# noinspection PyPep8Naming,SqlResolve,SqlNoDataSourceInspection
class rr:
    @staticmethod
    async def command(
            inter: ApplicationCommandInteraction,
            emoji: str,
            role: str,
            title: str,
            description: str,
    ) -> None:
        guild = _guild(inter)
        db = dpys.get_database("rr")
        await inter.send(
            "Attempting to create reaction role...", ephemeral=dpys.EPHEMERAL
        )
        if len(title) > 256 or len(description) > 4096:
            await inter.followup.send(
                "The title or description is too long.", ephemeral=dpys.EPHEMERAL
            )
            return
        raw_emojis = [entry.strip() for entry in emoji.split(",") if entry.strip()]
        parsed_emojis = [discord.PartialEmoji.from_str(entry) for entry in raw_emojis]
        emoji_list = [str(entry) for entry in parsed_emojis]
        emoji_keys = {_emoji_key(entry) for entry in parsed_emojis}
        if not emoji_list or len(emoji_keys) != len(emoji_list):
            await inter.followup.send(
                "Provide one or more unique emojis.", ephemeral=dpys.EPHEMERAL
            )
            return
        role_values = [entry.strip() for entry in role.split(",") if entry.strip()]
        try:
            role_ids = [
                int(entry.replace("<", "").replace(">", "").replace("@", "").replace("&", ""))
                for entry in role_values
            ]
        except ValueError:
            await inter.followup.send("Invalid role.", ephemeral=dpys.EPHEMERAL)
            return
        role_list = [guild.get_role(role_id) for role_id in role_ids]
        if len(role_list) != len(emoji_list):
            await inter.followup.send(
                "Emoji list must be the same length as role list.",
                ephemeral=dpys.EPHEMERAL,
            )
            return
        if any(role_obj is None for role_obj in role_list):
            await inter.followup.send("Invalid role.", ephemeral=dpys.EPHEMERAL)
            return
        roles = [role_obj for role_obj in role_list if role_obj is not None]
        bot_member = guild.me
        if bot_member is None or not bot_member.guild_permissions.manage_roles:
            await inter.followup.send(
                "I need the Manage Roles permission to create reaction roles.",
                ephemeral=dpys.EPHEMERAL,
            )
            return
        if any(not role_obj.is_assignable() for role_obj in roles):
            await inter.followup.send(
                "I cannot assign one or more of those roles.",
                ephemeral=dpys.EPHEMERAL,
            )
            return
        author_top_role = getattr(inter.author, "top_role", None)
        author_top_position = getattr(author_top_role, "position", None)
        if inter.author.id != guild.owner_id and (
                not isinstance(author_top_position, int)
                or any(role_obj.position >= author_top_position for role_obj in roles)
        ):
            await inter.followup.send(
                "You cannot create a reaction role above your highest role.",
                ephemeral=dpys.EPHEMERAL,
            )
            return

        embed = discord.Embed(
            title=title, color=dpys.COLOR, description=description
        )
        try:
            msg = await inter.channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            await inter.followup.send("Invalid emoji or embed.", ephemeral=dpys.EPHEMERAL)
            return
        try:
            for emoji_value in emoji_list:
                await msg.add_reaction(emoji_value)
        except (discord.Forbidden, discord.HTTPException):
            with contextlib.suppress(discord.HTTPException):
                await msg.delete()
            await inter.followup.send("Invalid emoji or embed.", ephemeral=dpys.EPHEMERAL)
            return

        rows = [
            (
                str(msg.id),
                emoji_value,
                str(role_obj.id),
                str(guild.id),
                str(inter.channel.id),
            )
            for emoji_value, role_obj in zip(emoji_list, roles)
        ]
        try:
            await db.executemany(
                "INSERT INTO rr (msg_id,emoji,role,guild,channel) VALUES (?,?,?,?,?)",
                rows,
            )
            await db.commit()
        except sqlite3.Error:
            await db.rollback()
            with contextlib.suppress(discord.HTTPException):
                await msg.delete()
            await inter.followup.send(
                "Could not save the reaction role.",
                ephemeral=dpys.EPHEMERAL,
            )
            return
        await inter.followup.send(
            "Successfully created the reaction role.", ephemeral=dpys.EPHEMERAL
        )

    @staticmethod
    async def add(payload: discord.RawReactionActionEvent, bot: commands.Bot) -> None:
        if payload.guild_id is None:
            return
        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return
        member = await _resolve_member(
            guild, payload.user_id, getattr(payload, "member", None)
        )
        if member is None or member.bot:
            return
        db = dpys.get_database("rr")
        stale_roles: list[str] = []
        async with db.execute(
                "SELECT emoji,role FROM rr WHERE guild = ? and msg_id = ?",
                (str(guild.id), str(payload.message_id)),
        ) as cursor:
            async for emoji_value, role_id in cursor:
                try:
                    role_obj = guild.get_role(int(role_id))
                except (TypeError, ValueError):
                    role_obj = None
                if role_obj is None:
                    stale_roles.append(role_id)
                elif _emoji_matches(emoji_value, payload.emoji):
                    try:
                        await member.add_roles(role_obj)
                    except (discord.Forbidden, discord.HTTPException):
                        return
        if stale_roles:
            await db.executemany(
                "DELETE FROM rr WHERE guild = ? and msg_id = ? and role = ?",
                [
                    (str(guild.id), str(payload.message_id), role_id)
                    for role_id in stale_roles
                ],
            )
            await db.commit()

    @staticmethod
    async def remove(
            payload: discord.RawReactionActionEvent, bot: commands.Bot
    ) -> None:
        if payload.guild_id is None:
            return
        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return
        member = await _resolve_member(guild, payload.user_id)
        if member is None or member.bot:
            return
        db = dpys.get_database("rr")
        stale_roles: list[str] = []
        async with db.execute(
                "SELECT emoji,role FROM rr WHERE guild = ? and msg_id = ?",
                (str(guild.id), str(payload.message_id)),
        ) as cursor:
            async for emoji_value, role_id in cursor:
                try:
                    role_obj = guild.get_role(int(role_id))
                except (TypeError, ValueError):
                    role_obj = None
                if role_obj is None:
                    stale_roles.append(role_id)
                elif _emoji_matches(emoji_value, payload.emoji):
                    try:
                        await member.remove_roles(role_obj)
                    except (discord.Forbidden, discord.HTTPException):
                        return
        if stale_roles:
            await db.executemany(
                "DELETE FROM rr WHERE guild = ? and msg_id = ? and role = ?",
                [
                    (str(guild.id), str(payload.message_id), role_id)
                    for role_id in stale_roles
                ],
            )
            await db.commit()

    @staticmethod
    async def clear_all(inter: ApplicationCommandInteraction) -> None:
        guild = str(_guild(inter).id)
        db = dpys.get_database("rr")
        cursor = await db.execute("DELETE FROM rr WHERE guild = ?", (guild,))
        await db.commit()
        message = (
            f"Deleted {cursor.rowcount} reaction role mapping(s) for this server."
            if cursor.rowcount
            else "There is no reaction role info for this server."
        )
        await inter.send(
            message,
            ephemeral=dpys.EPHEMERAL,
        )

    @staticmethod
    async def clear_one(
            inter: ApplicationCommandInteraction, message_id: int | str
    ) -> None:
        guild = str(_guild(inter).id)
        message_ids = [
            entry for entry in str(message_id).replace(" ", "").split(",") if entry
        ]
        if not message_ids:
            await inter.send("Provide at least one message ID.", ephemeral=dpys.EPHEMERAL)
            return
        db = dpys.get_database("rr")
        deleted = 0
        for entry in message_ids:
            cursor = await db.execute(
                "DELETE FROM rr WHERE guild = ? and msg_id = ?", (guild, entry)
            )
            deleted += max(cursor.rowcount, 0)
        await db.commit()
        message = (
            f"Deleted {deleted} reaction role mapping(s) with message ID(s): "
            f"{', '.join(message_ids)}"
            if deleted
            else "No reaction role info matched those message IDs."
        )
        await inter.send(
            message,
            ephemeral=dpys.EPHEMERAL,
        )

    @staticmethod
    async def clear_on_message_delete(message: discord.Message) -> None:
        if message.guild is None:
            return
        db = dpys.get_database("rr")
        guild = str(message.guild.id)
        message_id = str(message.id)
        await db.execute(
            "DELETE FROM rr WHERE msg_id = ? and guild = ?", (message_id, guild)
        )
        await db.commit()

    @staticmethod
    async def clear_on_raw_message_delete(
            payload: discord.RawMessageDeleteEvent,
    ) -> None:
        if payload.guild_id is None:
            return
        db = dpys.get_database("rr")
        await db.execute(
            "DELETE FROM rr WHERE msg_id = ? and guild = ?",
            (str(payload.message_id), str(payload.guild_id)),
        )
        await db.commit()

    @staticmethod
    async def clear_on_channel_delete(channel: discord.abc.GuildChannel) -> None:
        channel_id = channel.id
        guild = channel.guild.id
        db = dpys.get_database("rr")
        await db.execute(
            "DELETE FROM rr WHERE guild = ? and channel = ?",
            (str(guild), str(channel_id)),
        )
        await db.commit()

    @staticmethod
    async def clear_on_thread_delete(thread: discord.Thread) -> None:
        thread_id = thread.id
        guild = thread.guild.id
        db = dpys.get_database("rr")
        await db.execute(
            "DELETE FROM rr WHERE guild = ? and channel = ?",
            (str(guild), str(thread_id)),
        )
        await db.commit()

    @staticmethod
    async def clear_on_bulk_message_delete(
            payload: discord.RawBulkMessageDeleteEvent,
    ) -> None:
        ids = payload.message_ids
        guild = payload.guild_id
        if guild is None:
            return
        db = dpys.get_database("rr")
        await db.executemany(
            "DELETE FROM rr WHERE guild = ? and msg_id = ?",
            [(str(guild), str(message_id)) for message_id in ids],
        )
        await db.commit()

    class Delete(disnake.ui.Button):
        async def callback(self, inter: discord.MessageInteraction) -> None:
            await inter.response.defer()
            if self.view.navigation_lock.locked():
                return
            async with self.view.navigation_lock:
                current = self.view.list[
                    self.view.pos * self.view.count: self.view.pos * self.view.count
                                                     + self.view.count
                ][0]
                msg_id = current[2]
                channel = current[3]
                if inter.guild is None:
                    await inter.edit_original_message(
                        content="This control can only be used in a guild."
                    )
                    return
                db = dpys.get_database("rr")
                # noinspection SqlResolve,SqlNoDataSourceInspection
                await db.execute(
                    "DELETE FROM rr WHERE guild = ? and msg_id = ?",
                    (str(inter.guild.id), str(msg_id)),
                )
                await db.commit()
                self.view.list.remove(current)
                if channel is not None:
                    with contextlib.suppress(
                            discord.NotFound, discord.Forbidden, discord.HTTPException
                    ):
                        msg = await channel.fetch_message(msg_id)
                        await msg.delete()
                if len(self.view.list) == 0:
                    self.view.clear_items()
                    self.view.stop()
                    await inter.edit_original_message(
                        content="There are no reaction roles in this server.",
                        view=self.view,
                        embed=None,
                    )
                    self.view.clear_data()
                    return
                await self.view.reset()
                self.view.add_item(self)
                embed = await self.view.render_page()
                await inter.edit_original_message(embed=embed, view=self.view)

    @staticmethod
    async def display(inter: ApplicationCommandInteraction) -> None:
        guild_obj = _guild(inter)
        guild = str(guild_obj.id)
        db = dpys.get_database("rr")
        reaction_roles = []
        async with db.execute(
                "SELECT DISTINCT msg_id FROM rr WHERE guild = ? ORDER BY CAST(msg_id AS INTEGER)",
                (guild,),
        ) as cursor:
            async for (stored_message_id,) in cursor:
                async with db.execute(
                        "SELECT role,emoji,channel,msg_id FROM rr WHERE guild = ? and msg_id = ?",
                        (guild, stored_message_id),
                ) as result:
                    rows = await result.fetchall()
                if not rows:
                    continue
                roles = []
                emojis = []
                channel_id = rows[0][2]
                try:
                    msg_id = int(stored_message_id)
                    channel_id_int = int(channel_id)
                except (TypeError, ValueError):
                    continue
                for role_id, emoji_value, _, _ in rows:
                    try:
                        roles.append(guild_obj.get_role(int(role_id)))
                    except (TypeError, ValueError):
                        roles.append(None)
                    emojis.append(emoji_value)
                channel = guild_obj.get_channel_or_thread(channel_id_int)
                reaction_roles.append((roles, emojis, msg_id, channel))
        if reaction_roles:
            def page_embed(array, _, page_info):
                page = disnake.Embed(title="Reaction Roles", color=dpys.COLOR)
                page.add_field(
                    name="Roles",
                    value=" ".join(
                        role.mention if role is not None else "@deleted-role"
                        for role in array[0][0]
                    ),
                    inline=False,
                )
                page.add_field(
                    name="Emojis", value=" ".join(array[0][1]), inline=False
                )
                page.add_field(
                    name="Channel",
                    value=(
                        array[0][3].mention
                        if array[0][3] is not None
                        else "#deleted-channel"
                    ),
                    inline=False,
                )
                page.add_field(name="Message ID", value=array[0][2], inline=False)
                page.set_footer(text=f"Page {page_info[0]}/{page_info[1]}")
                return page

            view = ListScroller(1, reaction_roles, page_embed, inter)
            embed = page_embed(reaction_roles[0:1], 1, (1, len(reaction_roles)))
            delete_button = rr.Delete(
                label="Delete",
                style=disnake.ButtonStyle.red,
                custom_id=f"delete{id(view)}",
            )
            await view.start()
            view.add_item(delete_button)
            await inter.send(embed=embed, view=view, ephemeral=dpys.EPHEMERAL)
            return
        await inter.send(
            "There are no reaction roles in this server.", ephemeral=dpys.EPHEMERAL
        )
