import contextlib
import datetime
import typing
from typing import Union

import disnake as discord
from disnake import ApplicationCommandInteraction

import dpys
from .utils import get_discord_date


class admin:
    @staticmethod
    async def mute(
        inter: ApplicationCommandInteraction,
        member: discord.Member,
        role_add: int,
        role_remove: typing.Optional[int] = None,
        reason: str = None,
        msg: str = None,
    ) -> None:
        if inter.guild.get_role(role_add) in member.roles:
            await inter.send(
                f"{member.display_name} is already muted.",
                ephemeral=dpys.EPHEMERAL,
            )
            return
        if len(str(reason)) > 256:
            reason = reason[:253] + "..."
        if not isinstance(inter.guild.get_role(role_add), discord.Role):
            return
        await member.add_roles(inter.guild.get_role(role_add))
        if role_remove is not None:
            with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                await member.remove_roles(inter.guild.get_role(role_remove))
        await member.edit(reason=reason, voice_channel=None)
        if reason is None:
            await inter.send(
                msg or f"Muted {member.display_name}.", ephemeral=dpys.EPHEMERAL
            )
        else:
            await inter.send(
                msg or f"Muted {member.display_name}. Reason: {reason}",
                ephemeral=dpys.EPHEMERAL,
            )

    @staticmethod
    async def unmute(
        inter: ApplicationCommandInteraction,
        member: discord.Member,
        role_remove: int,
        role_add: typing.Optional[int] = None,
        msg: str = None,
    ) -> bool:
        if inter.guild.get_role(role_remove) not in member.roles:
            await inter.send(
                f"{member.display_name} is not muted.", ephemeral=dpys.EPHEMERAL
            )
            return False
        if not isinstance(inter.guild.get_role(role_remove), discord.Role):
            return False
        await member.remove_roles(inter.guild.get_role(role_remove))
        if role_add is not None:
            with contextlib.suppress(discord.Forbidden, discord.HTTPException):
                await member.add_roles(inter.guild.get_role(role_add))
        await inter.send(
            msg or f"Unmuted {member.display_name}.", ephemeral=dpys.EPHEMERAL
        )
        return True

    @staticmethod
    async def clear(
        inter: ApplicationCommandInteraction,
        amount: typing.Optional[int] = 99999999999999999,
        msg: str = None,
    ) -> int:
        limit = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            weeks=2
        )
        purged = await inter.channel.purge(limit=amount, after=limit)
        purged = len(purged)
        message = msg or (
            f"Cleared {purged} messages." if purged != 1 else f"Cleared {purged} message."
        )
        await inter.send(message, ephemeral=dpys.EPHEMERAL)
        return purged

    @staticmethod
    async def kick(
        inter: ApplicationCommandInteraction,
        member: discord.Member,
        reason: typing.Optional[str] = None,
        msg: str = None,
    ) -> None:
        if len(str(reason)) > 256:
            reason = reason[:253] + "..."
        await member.kick(reason=reason)
        if reason is None:
            message = msg or f"Kicked {member.display_name}."
        else:
            message = msg or f"Kicked {member.display_name}. Reason: {reason}"
        await inter.send(message, ephemeral=dpys.EPHEMERAL)

    @staticmethod
    async def ban(
        inter: ApplicationCommandInteraction,
        member: discord.User,
        reason: typing.Optional[str] = None,
        msg: str = None,
    ) -> None:
        if len(str(reason)) > 256:
            reason = reason[:253] + "..."
        await inter.guild.ban(member, reason=reason)
        if reason is None:
            message = msg or f"Banned {dpys.display_name(member)}."
        else:
            message = msg or f"Banned {dpys.display_name(member)}. Reason: {reason}"
        await inter.send(message, ephemeral=dpys.EPHEMERAL)

    @staticmethod
    async def timeout(
        inter: ApplicationCommandInteraction,
        member: discord.Member,
        duration: Union[float, datetime.timedelta] = None,
        until: datetime.datetime = None,
        reason: typing.Optional[str] = None,
        msg: str = None,
    ) -> None:
        if len(str(reason)) > 256:
            reason = reason[:253] + "..."
        if duration is not None:
            await member.timeout(duration=duration, reason=reason)
            if isinstance(duration, datetime.timedelta):
                end_timeout = get_discord_date(
                    (datetime.datetime.now() + duration).timestamp()
                )
            else:
                end_timeout = get_discord_date(
                    (
                        datetime.datetime.now() + datetime.timedelta(seconds=duration)
                    ).timestamp()
                )
        elif until is not None:
            await member.timeout(until=until, reason=reason)
            end_timeout = get_discord_date(until.timestamp())
        else:
            await member.edit(timeout=None)
            await inter.send(
                f"Removed timeout from {member.display_name}.",
                ephemeral=dpys.EPHEMERAL,
            )
            return
        if reason is None:
            message = msg or f"Timed out {member.display_name} until {end_timeout}."
        else:
            message = (
                msg
                or f"Timed out {member.display_name} until {end_timeout}. Reason: {reason}"
            )
        await inter.send(message, ephemeral=dpys.EPHEMERAL)

    @staticmethod
    async def softban(
        inter: ApplicationCommandInteraction,
        member: discord.Member,
        reason: typing.Optional[str] = None,
        msg: str = None,
    ) -> None:
        if len(str(reason)) > 256:
            reason = reason[:253] + "..."
        await member.ban(reason=reason)
        if reason is None:
            message = msg or f"Soft banned {dpys.display_name(member)}."
        else:
            message = (
                msg or f"Soft banned {dpys.display_name(member)}. Reason: {reason}"
            )
        await inter.send(message, ephemeral=dpys.EPHEMERAL)
        await inter.guild.unban(member)

    @staticmethod
    async def unban(
        inter: ApplicationCommandInteraction,
        member: discord.User,
        msg: str = None,
    ) -> bool:
        bans = inter.guild.bans()
        ban = [ban async for ban in bans if ban.user.id == member.id]
        if not ban:
            await inter.send(
                f"{dpys.display_name(member)} is not banned.",
                ephemeral=dpys.EPHEMERAL,
            )
            return False
        await inter.guild.unban(ban[0].user)
        await inter.send(
            msg or f"Unbanned {dpys.display_name(member)}.",
            ephemeral=dpys.EPHEMERAL,
        )
        return True
