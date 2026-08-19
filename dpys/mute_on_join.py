import disnake as discord

import dpys


def _require_assignable_role(guild: discord.Guild, role: discord.Role) -> None:
    if not isinstance(role, discord.Role):
        return
    bot_member = guild.me
    if bot_member is None or not bot_member.guild_permissions.manage_roles:
        raise ValueError("The bot requires Manage Roles to enforce muted members")
    if role.is_default() or role.managed or not role.is_assignable():
        raise ValueError(f"The bot cannot manage the configured role {role!s}")


# noinspection PyPep8Naming,SqlResolve,SqlNoDataSourceInspection
class mute_on_join:
    @staticmethod
    async def mute_add(guild: discord.Guild, member: discord.Member) -> None:
        guildid = str(guild.id)
        member_id = str(member.id)
        db = dpys.get_database("muted")
        await db.execute(
            "INSERT OR IGNORE INTO muted (name,guild) VALUES (?,?)",
            (member_id, guildid),
        )
        await db.commit()

    @staticmethod
    async def mute_remove(guild: discord.Guild, member: discord.Member) -> None:
        member_id = str(member.id)
        guildid = str(guild.id)
        db = dpys.get_database("muted")
        await db.execute(
            "DELETE FROM muted WHERE name = ? and guild = ?", (member_id, guildid)
        )
        await db.commit()

    @staticmethod
    async def mute_on_join(
            member: discord.Member, role_add: int, role_remove: int | None = None
    ) -> None:
        guildid = str(member.guild.id)
        db = dpys.get_database("muted")
        async with db.execute(
                "SELECT 1 FROM muted WHERE guild = ? and name = ?",
                (guildid, str(member.id)),
        ) as cursor:
            is_muted = await cursor.fetchone()
        if is_muted is None:
            return

        warnings_db = dpys.get_database("warnings")
        async with warnings_db.execute(
                """SELECT mute_role, restore_role
                   FROM tempmute
                   WHERE guild = ?
                     and member = ?
                     and state IN ('pending', 'active')""",
                (guildid, str(member.id)),
        ) as cursor:
            schedule_roles = await cursor.fetchone()
        if schedule_roles is not None and schedule_roles[0] is not None:
            try:
                role_add = int(schedule_roles[0])
                role_remove = (
                    None if schedule_roles[1] is None else int(schedule_roles[1])
                )
            except (TypeError, ValueError) as error:
                raise ValueError("The stored mute schedule has invalid role IDs") from error
        if role_remove is not None and role_add == role_remove:
            raise ValueError("The mute and restore roles must be different")
        muted_role = member.guild.get_role(role_add)
        if muted_role is None:
            raise ValueError("The configured mute role does not exist")
        _require_assignable_role(member.guild, muted_role)
        removed_role = None
        if role_remove is not None:
            removed_role = member.guild.get_role(role_remove)
            if removed_role is None:
                raise ValueError("The configured restore role does not exist")
            _require_assignable_role(member.guild, removed_role)
        await member.add_roles(muted_role)
        if removed_role is not None:
            await member.remove_roles(removed_role)

    @staticmethod
    async def manual_unmute_check(
            before: discord.Member,
            after: discord.Member | int,
            roleid: int | None = None,
    ) -> None:
        if roleid is None:
            # Preserve the old two-argument call without treating an unrelated
            # member update as proof that a moderator removed the mute role.
            return
        if isinstance(after, int):
            raise TypeError("after must be a Member")
        db = dpys.get_database("muted")
        guildid = str(after.guild.id)
        role = after.guild.get_role(roleid)
        if role is None:
            return
        memberid = str(after.id)
        if role not in before.roles or role in after.roles:
            return
        async with db.execute(
                "SELECT 1 FROM muted WHERE guild = ? and name = ?",
                (guildid, memberid),
        ) as cursor:
            if await cursor.fetchone() is None:
                return
        warnings_db = dpys.get_database("warnings")
        try:
            await warnings_db.execute(
                "DELETE FROM tempmute WHERE guild = ? and member = ?",
                (guildid, memberid),
            )
            await warnings_db.commit()
        except Exception:
            await warnings_db.rollback()
            raise
        try:
            await db.execute(
                "DELETE FROM muted WHERE guild = ? and name = ?",
                (guildid, memberid),
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
