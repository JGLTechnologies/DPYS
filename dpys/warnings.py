from __future__ import annotations

import asyncio
import contextlib
import datetime
import logging
import math
import sqlite3
import time
from typing import AsyncIterator, Awaitable, Callable, Mapping, Optional

import aiosqlite
import disnake
import disnake as discord
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

import dpys
from .mute_on_join import mute_on_join
from .utils import ListScroller

logger = logging.getLogger(__name__)
MAX_TIMEOUT_SECONDS = 28 * 24 * 60 * 60


class _InvalidSchedule(ValueError):
    """Stored schedule data cannot be processed without operator intervention."""


class _ScheduleLock:
    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.users = 0


_schedule_locks: dict[
    tuple[asyncio.AbstractEventLoop, str, str, str], _ScheduleLock
] = {}


@contextlib.asynccontextmanager
async def _schedule_guard(
        kind: str, guild_id: str | int, member_id: str | int
) -> AsyncIterator[None]:
    """Serialize one member's schedule updates and expiry work."""
    key = (asyncio.get_running_loop(), kind, str(guild_id), str(member_id))
    entry = _schedule_locks.get(key)
    if entry is None:
        entry = _ScheduleLock()
        _schedule_locks[key] = entry
    entry.users += 1
    acquired = False
    try:
        await entry.lock.acquire()
        acquired = True
        yield
    finally:
        if acquired:
            entry.lock.release()
        entry.users -= 1
        if entry.users == 0 and _schedule_locks.get(key) is entry:
            del _schedule_locks[key]


def _schedule_timestamp(value: object) -> float:
    """Read current epoch schedules and legacy ISO datetime values."""
    if not isinstance(value, (str, int, float)):
        raise _InvalidSchedule("Invalid stored punishment time")
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.datetime.fromisoformat(str(value))
            timestamp = parsed.timestamp()
        except (TypeError, ValueError, OverflowError) as error:
            raise _InvalidSchedule("Invalid stored punishment time") from error
    if not math.isfinite(timestamp):
        raise _InvalidSchedule("Stored punishment time must be finite")
    return timestamp


def _require_manageable_role(guild: discord.Guild, role: discord.Role) -> None:
    # Unit-test doubles need only model role identity; real Discord roles must
    # pass the same permission and hierarchy checks as the admin helpers.
    if not isinstance(role, discord.Role):
        return
    bot_member = guild.me
    if (
            bot_member is None
            or not bot_member.guild_permissions.manage_roles
            or role.is_default()
            or role.managed
            or not role.is_assignable()
    ):
        raise ValueError(f"The bot cannot manage the configured role {role!s}")


# noinspection PyPep8Naming,SqlResolve,SqlNoDataSourceInspection,PyBroadException
class warnings:
    @staticmethod
    async def _run_before(
            before: Callable[
                        [int, "warnings.Punishment", discord.Member],
                        Awaitable[Optional[discord.Message]],
                    ]
                    | None,
            warnings_number: int,
            punishment: "warnings.Punishment",
            member: discord.Member,
    ) -> Optional[discord.Message]:
        if before is None:
            return None
        return await before(warnings_number, punishment, member)

    class Punishment:
        def __init__(
                self, punishment: str, duration: float | int | None = None
        ):
            if punishment not in {
                "temp_ban",
                "temp_mute",
                "mute",
                "ban",
                "kick",
                "timeout",
            }:
                raise ValueError("Invalid punishment")
            temporary = punishment.startswith("temp_") or punishment == "timeout"
            if temporary and (
                    isinstance(duration, bool)
                    or not isinstance(duration, (int, float))
                    or not math.isfinite(duration)
                    or duration <= 0
            ):
                raise ValueError(
                    "duration must be a positive number for temporary punishments"
                )
            if punishment == "timeout" and duration > MAX_TIMEOUT_SECONDS:
                raise ValueError("timeouts cannot be longer than 28 days")
            self.punishment = punishment
            if temporary:
                assert isinstance(duration, (int, float)) and not isinstance(
                    duration, bool
                )
                self.duration = float(duration)
            else:
                self.duration = None

    @staticmethod
    async def warn(
            inter: ApplicationCommandInteraction,
            member: discord.Member,
            reason: str | None = None,
            expires: float | int | None = -1,
    ) -> None:
        if inter.guild is None:
            raise ValueError("This helper can only be used in a guild")
        db = dpys.get_database("warnings")
        reason = reason.strip() if reason else None
        if reason is not None and len(reason) > 256:
            reason = reason[:253] + "..."
        reason_str = reason or "No reason provided."
        if expires is None:
            expires = -1
        if isinstance(expires, bool) or not isinstance(expires, (int, float)):
            raise TypeError("expires must be a Unix timestamp or -1")
        if not math.isfinite(expires):
            raise ValueError("expires must be finite")
        guildid = str(inter.guild.id)
        user = member
        member_id = str(member.id)
        async with db.execute(
                "INSERT INTO warnings (member_id,guild,reason,expires) VALUES (?,?,?,?)",
                (member_id, guildid, reason_str, expires),
        ):
            pass
        await db.commit()
        if reason is None:
            msg = f"Warned {user.display_name}."
        else:
            msg = f"Warned {user.display_name}. Reason: {reason}"
        await inter.send(msg, ephemeral=dpys.EPHEMERAL)

    @staticmethod
    async def warnings_list(guild: int, member_id: int) -> list[str]:
        db = dpys.get_database("warnings")
        async with db.execute(
                """SELECT reason
                   FROM warnings
                   WHERE guild = ?
                     and member_id = ?
                     and (expires = -1 or expires > ?)
                   ORDER BY id""",
                (str(guild), str(member_id), time.time()),
        ) as cursor:
            return [entry[0] async for entry in cursor]

    @staticmethod
    async def warnings(
            inter: ApplicationCommandInteraction,
            member: discord.Member,
            warn_num: int = 0,
    ) -> None:
        if inter.guild is None:
            raise ValueError("This helper can only be used in a guild")
        if warn_num < 0:
            await inter.send(
                "Warning number must be zero or greater.", ephemeral=dpys.EPHEMERAL
            )
            return
        warn_list = await warnings.warnings_list(inter.guild.id, member.id)
        total = len(warn_list)
        if total == 0:
            await inter.send(
                f"{member.display_name} has no warnings.", ephemeral=dpys.EPHEMERAL
            )
            return
        if warn_num > total:
            await inter.send(
                f"{member.display_name} does not have that many.",
                ephemeral=dpys.EPHEMERAL,
            )
            return
        if warn_num:
            embed = discord.Embed(
                color=dpys.COLOR, title=f"{member.display_name}'s Warnings"
            )
            embed.add_field(
                name=f"Warning #{warn_num}",
                value=f"Reason: {warn_list[warn_num - 1]}",
                inline=False,
            )
            embed.set_footer(text=f"Total Warnings: {total}")
            await inter.send(embed=embed, ephemeral=dpys.EPHEMERAL)
            return

        def page_embed(array, start_num, page_info):
            page = disnake.Embed(
                title=f"{member.display_name}'s Warnings", color=dpys.COLOR
            )
            for index, warning in enumerate(array):
                page.add_field(
                    name=f"Warning #{index + start_num}",
                    value=f"Reason: {warning}",
                    inline=False,
                )
            page.set_footer(
                text=(
                    f"Page {page_info[0]}/{page_info[1]} | "
                    f"Total Warnings: {total}"
                )
            )
            return page

        view = ListScroller(5, warn_list, page_embed, inter)
        embed = page_embed(warn_list[0:5], 1, (1, math.ceil(total / 5)))
        await view.start()
        await inter.send(embed=embed, view=view, ephemeral=dpys.EPHEMERAL)

    @staticmethod
    async def unwarn(
            inter: ApplicationCommandInteraction,
            member: discord.Member,
            number: int | str,
    ) -> bool:
        if inter.guild is None:
            raise ValueError("This helper can only be used in a guild")
        user = member
        guild = str(inter.guild.id)
        member_id = str(member.id)
        number = str(number).lower()
        db = dpys.get_database("warnings")
        async with db.execute(
                """SELECT id
                   FROM warnings
                   WHERE guild = ?
                     and member_id = ?
                     and (expires = -1 or expires > ?)
                   ORDER BY id""",
                (guild, member_id, time.time()),
        ) as cursor:
            warning_ids = [entry[0] async for entry in cursor]
        if not warning_ids:
            await inter.send(
                f"{user.display_name} has no warnings.", ephemeral=dpys.EPHEMERAL
            )
            return False
        if number == "all":
            async with db.execute(
                    "DELETE FROM warnings WHERE guild = ? and member_id = ?",
                    (guild, member_id),
            ):
                pass
            await db.commit()
            await inter.send(
                f"Cleared all warnings from {user.display_name}.",
                ephemeral=dpys.EPHEMERAL,
            )
            return True
        try:
            requested = sorted(
                {int(entry) for entry in number.replace(" ", "").split(",")}
            )
        except ValueError:
            await inter.send("Warning numbers must be integers.", ephemeral=dpys.EPHEMERAL)
            return False
        if not requested or requested[0] < 1 or requested[-1] > len(warning_ids):
            await inter.send(
                f"{user.display_name} does not have that many warnings.",
                ephemeral=dpys.EPHEMERAL,
            )
            return False
        ids_to_delete = [warning_ids[index - 1] for index in requested]
        await db.executemany(
            "DELETE FROM warnings WHERE id = ?",
            [(warning_id,) for warning_id in ids_to_delete],
        )
        await db.commit()
        if len(requested) == 1:
            message = f"Cleared {user.display_name}'s #{requested[0]} warning."
        else:
            message = (
                f"Cleared warnings {', '.join(map(str, requested))} "
                f"from {user.display_name}."
            )
        await inter.send(message, ephemeral=dpys.EPHEMERAL)
        return True

    @staticmethod
    async def punish(
            inter: ApplicationCommandInteraction,
            member: discord.Member,
            punishments: Mapping[int, Punishment],
            add_role: int | None = None,
            remove_role: int | None = None,
            before: Callable[
                        [int, Punishment, discord.Member],
                        Awaitable[Optional[discord.Message]],
                    ]
                    | None = None,
    ) -> None:
        if inter.guild is None:
            raise ValueError("This helper can only be used in a guild")
        member_id = str(member.id)
        guild_id = str(inter.guild.id)
        db = dpys.get_database("warnings")
        async with db.execute(
                """SELECT COUNT(*)
                   FROM warnings
                   WHERE guild = ?
                     and member_id = ?
                     and (expires = -1 or expires > ?)""",
                (guild_id, member_id, time.time()),
        ) as cursor:
            row = await cursor.fetchone()
        warnings_number = row[0] if row is not None else 0
        punishment = punishments.get(warnings_number)
        if punishment is None:
            return
        reason = f"You have received {warnings_number} warning(s)."
        schedule_kind = (
            punishment.punishment
            if punishment.punishment in {"temp_ban", "temp_mute"}
            else None
        )
        guard = (
            _schedule_guard(schedule_kind, guild_id, member_id)
            if schedule_kind is not None
            else contextlib.nullcontext()
        )

        async with guard:
            callback_message = None
            applied_mute_role: Optional[discord.Role] = None
            removed_role: Optional[discord.Role] = None
            added_mute_record = False
            created_schedule = False
            previous_temp_mute: tuple | None = None
            muted_db: Optional[aiosqlite.Connection] = None

            try:
                callback_message = await warnings._run_before(
                    before, warnings_number, punishment, member
                )
                if punishment.punishment == "temp_ban":
                    if punishment.duration is None:
                        raise RuntimeError("temporary punishment is missing a duration")
                    async with db.execute(
                            "SELECT time,state FROM tempban "
                            "WHERE guild = ? and member = ?",
                            (guild_id, member_id),
                    ) as cursor:
                        previous_temp_ban = await cursor.fetchone()
                    expires_at = time.time() + punishment.duration
                    await db.execute(
                        """INSERT INTO tempban (guild, member, time, state)
                           VALUES (?, ?, ?, 'pending')
                           ON CONFLICT(guild,member) DO UPDATE
                               SET time  = excluded.time,
                                   state = 'pending'""",
                        (guild_id, member_id, expires_at),
                    )
                    await db.commit()
                    try:
                        await member.ban(reason=reason)
                    except Exception:
                        await db.rollback()
                        try:
                            if previous_temp_ban is None:
                                await db.execute(
                                    "DELETE FROM tempban "
                                    "WHERE guild = ? and member = ?",
                                    (guild_id, member_id),
                                )
                            else:
                                await db.execute(
                                    """UPDATE tempban
                                       SET time  = ?,
                                           state = ?
                                       WHERE guild = ?
                                         and member = ?""",
                                    (
                                        previous_temp_ban[0],
                                        previous_temp_ban[1],
                                        guild_id,
                                        member_id,
                                    ),
                                )
                            await db.commit()
                        except sqlite3.Error:
                            await db.rollback()
                            logger.exception(
                                "Could not restore the previous temp-ban schedule"
                            )
                        raise
                    await db.execute(
                        """UPDATE tempban
                           SET state = 'active'
                           WHERE guild = ?
                             and member = ?""",
                        (guild_id, member_id),
                    )
                    await db.commit()
                    return
                if punishment.punishment == "ban":
                    await member.ban(reason=reason)
                    return
                if punishment.punishment == "kick":
                    await member.kick(reason=reason)
                    return
                if punishment.punishment == "timeout":
                    await member.timeout(duration=punishment.duration, reason=reason)
                    return

                if punishment.punishment == "temp_mute":
                    if punishment.duration is None:
                        raise RuntimeError("temporary punishment is missing a duration")
                    async with db.execute(
                            """SELECT time,
                                      mute_role,
                                      restore_role,
                                      had_mute_role,
                                      had_restore_role,
                                      had_mute_record,
                                      state
                               FROM tempmute
                               WHERE guild = ?
                                 and member = ?""",
                            (guild_id, member_id),
                    ) as cursor:
                        previous_temp_mute = await cursor.fetchone()

                use_persisted_roles = (
                        previous_temp_mute is not None
                        and str(previous_temp_mute[6]) in {"pending", "active"}
                        and previous_temp_mute[1] is not None
                )
                if use_persisted_roles:
                    assert previous_temp_mute is not None
                    try:
                        mute_role_id = int(previous_temp_mute[1])
                        restore_role_id = (
                            None
                            if previous_temp_mute[2] is None
                            else int(previous_temp_mute[2])
                        )
                    except (TypeError, ValueError) as error:
                        raise _InvalidSchedule(
                            "A temp-mute schedule contains an invalid role ID"
                        ) from error
                else:
                    if add_role is None:
                        raise ValueError(
                            "A valid mute role is required for mute punishments"
                        )
                    mute_role_id = add_role
                    restore_role_id = remove_role

                if restore_role_id is not None and mute_role_id == restore_role_id:
                    raise ValueError("The mute and restore roles must be different")
                muted_role = inter.guild.get_role(mute_role_id)
                if muted_role is None:
                    raise ValueError("A valid mute role is required for mute punishments")
                _require_manageable_role(inter.guild, muted_role)
                restored_role = (
                    inter.guild.get_role(restore_role_id)
                    if restore_role_id is not None
                    else None
                )
                if restore_role_id is not None and restored_role is None:
                    raise ValueError("remove_role does not identify a valid role")
                if restored_role is not None:
                    _require_manageable_role(inter.guild, restored_role)

                current_muted_db = dpys.get_database("muted")
                muted_db = current_muted_db
                async with current_muted_db.execute(
                        "SELECT 1 FROM muted WHERE guild = ? and name = ?",
                        (guild_id, member_id),
                ) as cursor:
                    mute_record_exists = await cursor.fetchone() is not None

                if previous_temp_mute is not None and str(
                        previous_temp_mute[6]
                ) in {"legacy", "pending", "active"}:
                    had_mute_role = bool(int(previous_temp_mute[3]))
                    had_restore_role = bool(int(previous_temp_mute[4]))
                    had_mute_record = bool(int(previous_temp_mute[5]))
                else:
                    had_mute_role = muted_role in member.roles
                    had_restore_role = (
                            restored_role is not None and restored_role in member.roles
                    )
                    had_mute_record = mute_record_exists

                # If state was manually removed, this new punishment owns the
                # repair and must undo it when the new duration expires.
                if muted_role not in member.roles:
                    had_mute_role = False
                if restored_role is not None and restored_role in member.roles:
                    had_restore_role = True
                if not mute_record_exists:
                    had_mute_record = False

                if punishment.punishment == "temp_mute":
                    created_schedule = previous_temp_mute is None
                    await db.execute(
                        """INSERT INTO tempmute
                           (guild, member, time, mute_role, restore_role,
                            had_mute_role, had_restore_role, had_mute_record, state)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                           ON CONFLICT(guild,member) DO UPDATE SET time             = excluded.time,
                                                                   mute_role        = excluded.mute_role,
                                                                   restore_role     = excluded.restore_role,
                                                                   had_mute_role    = excluded.had_mute_role,
                                                                   had_restore_role = excluded.had_restore_role,
                                                                   had_mute_record  = excluded.had_mute_record,
                                                                   state            = 'pending'""",
                        (
                            guild_id,
                            member_id,
                            time.time() + punishment.duration,
                            str(muted_role.id),
                            str(restored_role.id) if restored_role is not None else None,
                            int(had_mute_role),
                            int(had_restore_role),
                            int(had_mute_record),
                        ),
                    )
                    await db.commit()

                if muted_role not in member.roles:
                    await member.add_roles(muted_role, reason=reason)
                    applied_mute_role = muted_role
                if restored_role is not None and restored_role in member.roles:
                    await member.remove_roles(restored_role, reason=reason)
                    removed_role = restored_role
                if not mute_record_exists:
                    await mute_on_join.mute_add(inter.guild, member)
                    added_mute_record = True
                if punishment.punishment == "temp_mute":
                    await db.execute(
                        """UPDATE tempmute
                           SET state = 'active'
                           WHERE guild = ?
                             and member = ?""",
                        (guild_id, member_id),
                    )
                    await db.commit()
            except Exception:
                with contextlib.suppress(sqlite3.Error):
                    await db.rollback()
                if muted_db is not None:
                    with contextlib.suppress(sqlite3.Error):
                        await muted_db.rollback()
                compensation_failed = False
                if applied_mute_role is not None:
                    try:
                        await member.remove_roles(applied_mute_role, reason=reason)
                    except (discord.Forbidden, discord.HTTPException):
                        compensation_failed = True
                if removed_role is not None:
                    try:
                        await member.add_roles(removed_role, reason=reason)
                    except (discord.Forbidden, discord.HTTPException):
                        compensation_failed = True
                if added_mute_record:
                    try:
                        await mute_on_join.mute_remove(inter.guild, member)
                    except sqlite3.Error:
                        compensation_failed = True
                if punishment.punishment == "temp_mute" and (
                        created_schedule or previous_temp_mute is not None
                ):
                    try:
                        if compensation_failed:
                            raise RuntimeError("punishment compensation was incomplete")
                        if previous_temp_mute is None:
                            await db.execute(
                                "DELETE FROM tempmute "
                                "WHERE guild = ? and member = ?",
                                (guild_id, member_id),
                            )
                        else:
                            await db.execute(
                                """INSERT INTO tempmute
                                   (guild, member, time, mute_role, restore_role,
                                    had_mute_role, had_restore_role,
                                    had_mute_record, state)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                   ON CONFLICT(guild,member) DO UPDATE SET time             = excluded.time,
                                                                           mute_role        = excluded.mute_role,
                                                                           restore_role     = excluded.restore_role,
                                                                           had_mute_role    = excluded.had_mute_role,
                                                                           had_restore_role = excluded.had_restore_role,
                                                                           had_mute_record  = excluded.had_mute_record,
                                                                           state            = excluded.state""",
                                (guild_id, member_id, *previous_temp_mute),
                            )
                        await db.commit()
                    except (sqlite3.Error, RuntimeError):
                        await db.rollback()
                if callback_message is not None:
                    with contextlib.suppress(discord.HTTPException):
                        await callback_message.delete()
                raise

    @staticmethod
    async def _process_temp_mute_schedule(
            bot: commands.BotBase,
            add_role_func: Callable[[int], Awaitable[int | None]],
            remove_role_func: Callable[[int], Awaitable[int | None]] | None,
            schedule: tuple,
    ) -> None:
        (
            stored_guild_id,
            stored_member_id,
            stored_time,
            stored_mute_role,
            stored_restore_role,
            stored_had_mute_role,
            stored_had_restore_role,
            stored_had_mute_record,
            state,
        ) = schedule
        try:
            guild_id = int(stored_guild_id)
            member_id = int(stored_member_id)
        except (TypeError, ValueError) as error:
            raise _InvalidSchedule("A temp-mute schedule has invalid IDs") from error
        expires_at = _schedule_timestamp(stored_time)
        expired = time.time() >= expires_at
        state = str(state)
        if state not in {"legacy", "pending", "active"}:
            raise _InvalidSchedule(f"Unknown temp-mute state: {state}")
        if state in {"legacy", "active"} and not expired:
            return

        guild = bot.get_guild(guild_id)
        if guild is None:
            return
        member = guild.get_member(member_id)
        if member is None:
            try:
                member = await guild.fetch_member(member_id)
            except discord.NotFound:
                if not expired:
                    return
                if not bool(int(stored_had_mute_record)):
                    muted_db = dpys.get_database("muted")
                    await muted_db.execute(
                        "DELETE FROM muted WHERE guild = ? and name = ?",
                        (str(guild_id), str(member_id)),
                    )
                    await muted_db.commit()
                db = dpys.get_database("warnings")
                await db.execute(
                    "DELETE FROM tempmute WHERE guild = ? and member = ?",
                    (str(guild_id), str(member_id)),
                )
                await db.commit()
                return
            except (discord.Forbidden, discord.HTTPException):
                return

        if state == "legacy":
            mute_role_id = await add_role_func(guild_id)
            restore_role_id = (
                None
                if remove_role_func is None
                else await remove_role_func(guild_id)
            )
        else:
            mute_role_id = stored_mute_role
            restore_role_id = stored_restore_role
        if isinstance(mute_role_id, bool) or mute_role_id is None:
            error_type = ValueError if state == "legacy" else _InvalidSchedule
            raise error_type("A temp-mute schedule has no valid mute role")
        try:
            mute_role_id = int(mute_role_id)
            if isinstance(restore_role_id, bool):
                raise TypeError
            restore_role_id = (
                None if restore_role_id is None else int(restore_role_id)
            )
        except (TypeError, ValueError) as error:
            if state == "legacy":
                raise ValueError("A role callback returned an invalid role ID") from error
            raise _InvalidSchedule(
                "A temp-mute schedule contains an invalid role ID"
            ) from error
        if restore_role_id == mute_role_id:
            error_type = ValueError if state == "legacy" else _InvalidSchedule
            raise error_type("A temp-mute schedule uses the same role twice")

        try:
            had_mute_role = bool(int(stored_had_mute_role))
            had_restore_role = bool(int(stored_had_restore_role))
            had_mute_record = bool(int(stored_had_mute_record))
        except (TypeError, ValueError) as error:
            raise _InvalidSchedule(
                "A temp-mute schedule contains invalid ownership flags"
            ) from error
        mute_role = guild.get_role(mute_role_id)
        restored_role = (
            None if restore_role_id is None else guild.get_role(restore_role_id)
        )
        db = dpys.get_database("warnings")

        if state == "pending" and not expired:
            if mute_role is None:
                raise _InvalidSchedule("The stored mute role no longer exists")
            if not had_mute_role and mute_role not in member.roles:
                await member.add_roles(mute_role)
            if (
                    had_restore_role
                    and restored_role is not None
                    and restored_role in member.roles
            ):
                await member.remove_roles(restored_role)
            if not had_mute_record:
                await mute_on_join.mute_add(guild, member)
            await db.execute(
                "UPDATE tempmute SET state = 'active' WHERE guild = ? and member = ?",
                (str(guild_id), str(member_id)),
            )
            await db.commit()
            return

        if not had_mute_role and mute_role is not None and mute_role in member.roles:
            await member.remove_roles(mute_role)
        if (
                had_restore_role
                and restored_role is not None
                and restored_role not in member.roles
        ):
            await member.add_roles(restored_role)
        if not had_mute_record:
            await mute_on_join.mute_remove(guild, member)
        await db.execute(
            "DELETE FROM tempmute WHERE guild = ? and member = ?",
            (str(guild_id), str(member_id)),
        )
        await db.commit()

    @staticmethod
    async def temp_mute_loop(
            bot: commands.BotBase,
            add_role_func: Callable[[int], Awaitable[int | None]],
            remove_role_func: Callable[[int], Awaitable[int | None]] | None = None,
    ) -> None:
        db = dpys.get_database("warnings")
        async with db.execute("SELECT guild,member FROM tempmute") as cursor:
            schedule_keys = await cursor.fetchall()
        for stored_guild_id, stored_member_id in schedule_keys:
            async with _schedule_guard(
                    "temp_mute", stored_guild_id, stored_member_id
            ):
                async with db.execute(
                        """SELECT guild,
                                  member,
                                  time,
                                  mute_role,
                                  restore_role,
                                  had_mute_role,
                                  had_restore_role,
                                  had_mute_record,
                                  state
                           FROM tempmute
                           WHERE guild = ?
                             and member = ?""",
                        (stored_guild_id, stored_member_id),
                ) as cursor:
                    schedule = await cursor.fetchone()
                if schedule is None or str(schedule[8]) == "invalid":
                    continue
                try:
                    await warnings._process_temp_mute_schedule(
                        bot, add_role_func, remove_role_func, schedule
                    )
                except asyncio.CancelledError:
                    raise
                except _InvalidSchedule:
                    await db.rollback()
                    await dpys.get_database("muted").rollback()
                    await db.execute(
                        """UPDATE tempmute
                           SET state = 'invalid'
                           WHERE guild = ?
                             and member = ?""",
                        (stored_guild_id, stored_member_id),
                    )
                    await db.commit()
                    logger.exception(
                        "Disabled invalid temp-mute schedule for guild=%r member=%r",
                        stored_guild_id,
                        stored_member_id,
                    )
                # Isolate user callback and Discord failures to this row.
                # noinspection PyBroadException
                except Exception:
                    await db.rollback()
                    await dpys.get_database("muted").rollback()
                    logger.exception(
                        "Could not process temp-mute schedule for guild=%r member=%r",
                        stored_guild_id,
                        stored_member_id,
                    )

    @staticmethod
    async def _process_temp_ban_schedule(
            bot: commands.BotBase, schedule: tuple
    ) -> None:
        stored_guild_id, stored_member_id, stored_time, state = schedule
        try:
            guild_id = int(stored_guild_id)
            member_id = int(stored_member_id)
        except (TypeError, ValueError) as error:
            raise _InvalidSchedule("A temp-ban schedule has invalid IDs") from error
        expires_at = _schedule_timestamp(stored_time)
        state = str(state)
        if state not in {"legacy", "pending", "active"}:
            raise _InvalidSchedule(f"Unknown temp-ban state: {state}")
        expired = time.time() >= expires_at
        if state in {"legacy", "active"} and not expired:
            return

        guild = bot.get_guild(guild_id)
        if guild is None:
            return
        db = dpys.get_database("warnings")
        if state == "pending" and not expired:
            try:
                await guild.ban(
                    discord.Object(id=member_id),
                    reason="Recovering a pending DPYS temporary ban",
                )
            except (discord.Forbidden, discord.HTTPException):
                return
            await db.execute(
                """UPDATE tempban
                   SET state = 'active'
                   WHERE guild = ?
                     and member = ?""",
                (str(guild_id), str(member_id)),
            )
            await db.commit()
            return

        try:
            await guild.unban(discord.Object(id=member_id))
        except discord.NotFound:
            pass
        except (discord.Forbidden, discord.HTTPException):
            return
        await db.execute(
            "DELETE FROM tempban WHERE guild = ? and member = ?",
            (str(guild_id), str(member_id)),
        )
        await db.commit()

    @staticmethod
    async def temp_ban_loop(bot: commands.BotBase) -> None:
        db = dpys.get_database("warnings")
        async with db.execute("SELECT guild,member FROM tempban") as cursor:
            schedule_keys = await cursor.fetchall()
        for stored_guild_id, stored_member_id in schedule_keys:
            async with _schedule_guard(
                    "temp_ban", stored_guild_id, stored_member_id
            ):
                async with db.execute(
                        """SELECT guild, member, time, state
                           FROM tempban
                           WHERE guild = ?
                             and member = ?""",
                        (stored_guild_id, stored_member_id),
                ) as cursor:
                    schedule = await cursor.fetchone()
                if schedule is None or str(schedule[3]) == "invalid":
                    continue
                try:
                    await warnings._process_temp_ban_schedule(bot, schedule)
                except asyncio.CancelledError:
                    raise
                except _InvalidSchedule:
                    await db.rollback()
                    await db.execute(
                        """UPDATE tempban
                           SET state = 'invalid'
                           WHERE guild = ?
                             and member = ?""",
                        (stored_guild_id, stored_member_id),
                    )
                    await db.commit()
                    logger.exception(
                        "Disabled invalid temp-ban schedule for guild=%r member=%r",
                        stored_guild_id,
                        stored_member_id,
                    )
                # A Discord or database failure must not block later schedules.
                # noinspection PyBroadException
                except Exception:
                    await db.rollback()
                    logger.exception(
                        "Could not process temp-ban schedule for guild=%r member=%r",
                        stored_guild_id,
                        stored_member_id,
                    )

    @staticmethod
    async def expire_loop() -> None:
        db = dpys.get_database("warnings")
        await db.execute(
            "DELETE FROM warnings WHERE expires != -1 and expires <= ?",
            (time.time(),),
        )
        await db.commit()
