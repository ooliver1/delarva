# SPDX-License-Identifier: MIT
# pyright: reportImportCycles=false
from __future__ import annotations

from typing import Iterable, Union

from nextcord import Interaction, slash_command
from nextcord.ext.commands import AutoShardedBot, Bot, Cog

BotT = Union[Bot, AutoShardedBot]


__all__ = ("BotT", "Base", "setup")


class Base(Cog):
    def __init__(self, guild_ids: Iterable[int] | None = None):
        if guild_ids is not None:
            self.debug.guild_ids_to_rollout = set(guild_ids)
            self.debug.default_member_permissions = 8

    @slash_command()
    async def debug(self, interaction: Interaction):  # type: ignore
        ...


def setup(bot: Bot | AutoShardedBot, guild_ids: Iterable[int] | None = None):
    from . import eval, info

    del eval, info

    bot.add_cog(Base(guild_ids))
