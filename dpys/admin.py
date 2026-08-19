import datetime
import math

import disnake as discord
from disnake import ApplicationCommandInteraction

import dpys
from .utils import get_discord_date

MAX_TIMEOUT_SECONDS = 28 * 24 * 60 * 60


def _guild(inter: ApplicationCommandInteraction) -> discord.Guild:
    if inter.guild is None:
        raise ValueError("This helper can only be used in a guild")
    return inter.guild


def _truncate_reason(reason: str | None) -> str | None:
    if reason is None or len(reason) <= 256:
        return reason
    return reason[:253] + "..."


async def _defer_if_needed(inter: ApplicationCommandInteraction) -> bool:
    if inter.response.is_done():
        return False
    await inter.response.defer(ephemeral=dpys.EPHEMERAL)
    return True


async def _send_completion(
        inter: ApplicationCommandInteraction, message: str, deferred: bool
) -> None:
    if deferred:
        await inter.edit_original_response(content=message)
    else:
        await inter.send(message, ephemeral=dpys.EPHEMERAL)


async def _can_moderate(
        inter: ApplicationCommandInteraction,
        target: discord.Member,
        deferred: bool = False,
) -> bool:
    guild = _guild(inter)
    author = inter.author
    if target.guild.id != guild.id or not isinstance(author, discord.Member):
        await _send_completion(inter, "That member is not in this server.", deferred)
        return False
    if target.id == author.id or target.id == guild.owner_id:
        await _send_completion(inter, "You cannot moderate that member.", deferred)
        return False
    if author.id != guild.owner_id and target.top_role.position >= author.top_role.position:
        await _send_completion(
            inter,
            "You cannot moderate a member with an equal or higher role.",
            deferred,
        )
        return False
    bot_member = guild.me
    if bot_member is None or target.top_role.position >= bot_member.top_role.position:
        await _send_completion(
            inter,
            "I cannot moderate that member because of the role hierarchy.",
            deferred,
        )
        return False
    return True


def _can_manage_role(guild: discord.Guild, role: discord.Role) -> bool:
    bot_member = guild.me
    return bool(
        bot_member is not None
        and bot_member.guild_permissions.manage_roles
        and not role.is_default()
        and not role.managed
        and role.is_assignable()
    )


# noinspection PyPep8Naming
class admin:
    @staticmethod
    async def mute(
            inter: ApplicationCommandInteraction,
            member: discord.Member,
            role_add: int,
            role_remove: int | None = None,
            reason: str | None = None,
            msg: str | None = None,
    ) -> bool:
        guild = _guild(inter)
        if not await _can_moderate(inter, member):
            return False
        if role_remove is not None and role_add == role_remove:
            await inter.send(
                "The mute role and role to remove must be different.",
                ephemeral=dpys.EPHEMERAL,
            )
            return False
        muted_role = guild.get_role(role_add)
        if muted_role is None:
            await inter.send("Invalid mute role.", ephemeral=dpys.EPHEMERAL)
            return False
        restored_role = (
            guild.get_role(role_remove) if role_remove is not None else None
        )
        if role_remove is not None and restored_role is None:
            await inter.send("Invalid role to remove.", ephemeral=dpys.EPHEMERAL)
            return False
        if not _can_manage_role(guild, muted_role) or (
                restored_role is not None
                and not _can_manage_role(guild, restored_role)
        ):
            await inter.send(
                "I cannot manage one of those roles. Check Manage Roles and the role hierarchy.",
                ephemeral=dpys.EPHEMERAL,
            )
            return False
        already_muted = muted_role in member.roles
        if already_muted and (
                restored_role is None or restored_role not in member.roles
        ):
            await inter.send(
                f"{member.display_name} is already muted.",
                ephemeral=dpys.EPHEMERAL,
            )
            return True
        reason = _truncate_reason(reason)
        deferred = await _defer_if_needed(inter)
        added_mute_role = False
        try:
            if not already_muted:
                await member.add_roles(muted_role, reason=reason)
                added_mute_role = True
            if restored_role is not None and restored_role in member.roles:
                await member.remove_roles(restored_role, reason=reason)
        except (discord.Forbidden, discord.HTTPException):
            rollback_failed = False
            if added_mute_role:
                try:
                    await member.remove_roles(muted_role, reason=reason)
                except (discord.Forbidden, discord.HTTPException):
                    rollback_failed = True
            message = (
                "The mute only partially completed; check the member's roles."
                if rollback_failed
                else "I could not update all required roles, so the mute was cancelled."
            )
            await _send_completion(inter, message, deferred)
            return False
        if reason is None:
            message = msg or f"Muted {member.display_name}."
        else:
            message = msg or f"Muted {member.display_name}. Reason: {reason}"
        await _send_completion(inter, message, deferred)
        return True

    @staticmethod
    async def unmute(
            inter: ApplicationCommandInteraction,
            member: discord.Member,
            role_remove: int,
            role_add: int | None = None,
            msg: str | None = None,
    ) -> bool:
        guild = _guild(inter)
        if not await _can_moderate(inter, member):
            return False
        if role_add is not None and role_remove == role_add:
            await inter.send(
                "The mute role and role to restore must be different.",
                ephemeral=dpys.EPHEMERAL,
            )
            return False
        muted_role = guild.get_role(role_remove)
        if muted_role is None:
            await inter.send("Invalid mute role.", ephemeral=dpys.EPHEMERAL)
            return False
        restored_role = guild.get_role(role_add) if role_add is not None else None
        if role_add is not None and restored_role is None:
            await inter.send("Invalid role to restore.", ephemeral=dpys.EPHEMERAL)
            return False
        if not _can_manage_role(guild, muted_role) or (
                restored_role is not None
                and not _can_manage_role(guild, restored_role)
        ):
            await inter.send(
                "I cannot manage one of those roles. Check Manage Roles and the role hierarchy.",
                ephemeral=dpys.EPHEMERAL,
            )
            return False
        if muted_role not in member.roles:
            await inter.send(
                f"{member.display_name} is not muted.", ephemeral=dpys.EPHEMERAL
            )
            return False
        deferred = await _defer_if_needed(inter)
        removed_mute_role = False
        try:
            await member.remove_roles(muted_role)
            removed_mute_role = True
            if restored_role is not None and restored_role not in member.roles:
                await member.add_roles(restored_role)
        except (discord.Forbidden, discord.HTTPException):
            rollback_failed = False
            if removed_mute_role:
                try:
                    await member.add_roles(muted_role)
                except (discord.Forbidden, discord.HTTPException):
                    rollback_failed = True
            message = (
                "The unmute only partially completed; check the member's roles."
                if rollback_failed
                else "I could not update all required roles, so the unmute was cancelled."
            )
            await _send_completion(inter, message, deferred)
            return False
        await _send_completion(
            inter, msg or f"Unmuted {member.display_name}.", deferred
        )
        return True

    @staticmethod
    async def clear(
            inter: ApplicationCommandInteraction,
            amount: int | None = 100,
            msg: str | None = None,
    ) -> int:
        amount = 100 if amount is None else amount
        if amount is not None and amount < 1:
            raise ValueError("amount must be greater than zero")
        if amount > 1000:
            raise ValueError("amount cannot be greater than 1000")
        _guild(inter)
        deferred = await _defer_if_needed(inter)
        purged = await inter.channel.purge(limit=amount)
        purged = len(purged)
        message = msg or (
            f"Cleared {purged} messages." if purged != 1 else f"Cleared {purged} message."
        )
        await _send_completion(inter, message, deferred)
        return purged

    @staticmethod
    async def kick(
            inter: ApplicationCommandInteraction,
            member: discord.Member,
            reason: str | None = None,
            msg: str | None = None,
    ) -> None:
        if not await _can_moderate(inter, member):
            return
        reason = _truncate_reason(reason)
        deferred = await _defer_if_needed(inter)
        await member.kick(reason=reason)
        if reason is None:
            message = msg or f"Kicked {member.display_name}."
        else:
            message = msg or f"Kicked {member.display_name}. Reason: {reason}"
        await _send_completion(inter, message, deferred)

    @staticmethod
    async def ban(
            inter: ApplicationCommandInteraction,
            member: discord.User,
            reason: str | None = None,
            msg: str | None = None,
    ) -> None:
        guild = _guild(inter)
        deferred = await _defer_if_needed(inter)
        target_member = (
            member if isinstance(member, discord.Member) else guild.get_member(member.id)
        )
        if target_member is None:
            try:
                target_member = await guild.fetch_member(member.id)
            except discord.NotFound:
                pass
            except (discord.Forbidden, discord.HTTPException):
                await _send_completion(
                    inter,
                    "I could not verify that user's server role hierarchy.",
                    deferred,
                )
                return
        if target_member is not None and not await _can_moderate(
                inter, target_member, deferred
        ):
            return
        reason = _truncate_reason(reason)
        await guild.ban(member, reason=reason)
        if reason is None:
            message = msg or f"Banned {dpys.display_name(member)}."
        else:
            message = msg or f"Banned {dpys.display_name(member)}. Reason: {reason}"
        await _send_completion(inter, message, deferred)

    @staticmethod
    async def timeout(
            inter: ApplicationCommandInteraction,
            member: discord.Member,
            duration: float | datetime.timedelta | None = None,
            until: datetime.datetime | None = None,
            reason: str | None = None,
            msg: str | None = None,
    ) -> None:
        if not await _can_moderate(inter, member):
            return
        reason = _truncate_reason(reason)
        if duration is not None and until is not None:
            raise ValueError("duration and until are mutually exclusive")
        if isinstance(duration, bool):
            raise TypeError("duration must be a number of seconds or a timedelta")
        if duration is not None and not isinstance(
                duration, (int, float, datetime.timedelta)
        ):
            raise TypeError("duration must be a number of seconds or a timedelta")
        if isinstance(duration, (int, float)) and (
                not math.isfinite(duration) or duration <= 0
        ):
            raise ValueError("duration must be a positive finite number")
        if isinstance(duration, (int, float)) and duration > MAX_TIMEOUT_SECONDS:
            raise ValueError("timeouts cannot be longer than 28 days")
        if isinstance(duration, datetime.timedelta) and not (
                0 < duration.total_seconds() <= MAX_TIMEOUT_SECONDS
        ):
            raise ValueError("timeout duration must be between 1 second and 28 days")
        normalized_until = None
        if until is not None:
            if not isinstance(until, datetime.datetime):
                raise TypeError("until must be a datetime")
            now = datetime.datetime.now(datetime.timezone.utc)
            normalized_until = (
                until.replace(tzinfo=datetime.timezone.utc)
                if until.tzinfo is None
                else until.astimezone(datetime.timezone.utc)
            )
            if not now < normalized_until <= now + datetime.timedelta(days=28):
                raise ValueError("timeout end must be within the next 28 days")
        deferred = await _defer_if_needed(inter)
        if duration is not None:
            await member.timeout(duration=duration, reason=reason)
            if isinstance(duration, datetime.timedelta):
                end_timeout = get_discord_date(
                    (datetime.datetime.now(datetime.timezone.utc) + duration).timestamp()
                )
            else:
                end_timeout = get_discord_date(
                    (
                            datetime.datetime.now(datetime.timezone.utc)
                            + datetime.timedelta(seconds=duration)
                    ).timestamp()
                )
        elif normalized_until is not None:
            await member.timeout(until=normalized_until, reason=reason)
            end_timeout = get_discord_date(normalized_until.timestamp())
        else:
            await member.timeout(duration=None, reason=reason)
            await _send_completion(
                inter, msg or f"Removed timeout from {member.display_name}.", deferred
            )
            return
        if reason is None:
            message = msg or f"Timed out {member.display_name} until {end_timeout}."
        else:
            message = (
                    msg
                    or f"Timed out {member.display_name} until {end_timeout}. Reason: {reason}"
            )
        await _send_completion(inter, message, deferred)

    @staticmethod
    async def softban(
            inter: ApplicationCommandInteraction,
            member: discord.Member,
            reason: str | None = None,
            msg: str | None = None,
    ) -> None:
        guild = _guild(inter)
        if not await _can_moderate(inter, member):
            return
        if member.guild.id != guild.id:
            raise ValueError("member does not belong to this interaction's guild")
        deferred = await _defer_if_needed(inter)
        reason = _truncate_reason(reason)
        await guild.ban(member, reason=reason)
        try:
            await guild.unban(member, reason=reason)
        except (discord.Forbidden, discord.HTTPException):
            await _send_completion(
                inter,
                "The ban succeeded, but the unban failed; the member is still banned.",
                deferred,
            )
            raise
        if reason is None:
            message = msg or f"Soft banned {dpys.display_name(member)}."
        else:
            message = (
                    msg or f"Soft banned {dpys.display_name(member)}. Reason: {reason}"
            )
        await _send_completion(inter, message, deferred)

    @staticmethod
    async def unban(
            inter: ApplicationCommandInteraction,
            member: discord.User,
            msg: str | None = None,
    ) -> bool:
        guild = _guild(inter)
        deferred = await _defer_if_needed(inter)
        try:
            entry = await guild.fetch_ban(member)
        except discord.NotFound:
            await _send_completion(
                inter,
                f"{dpys.display_name(member)} is not banned.",
                deferred,
            )
            return False
        await guild.unban(entry.user)
        await _send_completion(
            inter,
            msg or f"Unbanned {dpys.display_name(member)}.",
            deferred,
        )
        return True
