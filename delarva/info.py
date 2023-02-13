# SPDX-License-Identifier: MIT
# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false
from __future__ import annotations

import math
import platform

import nextcord
from nextcord import AutoShardedClient, Embed, Interaction
from nextcord.utils import format_dt, utcnow

from .base import Base, BotT

try:
    import psutil
except ImportError:
    psutil = None


UP_TIME = utcnow()


def human_size(byte: int) -> str:
    """
    Converts a number of bytes to an appropriately-scaled unit
    E.g.:
        1024 -> 1.00 KiB
        12345678 -> 11.77 MiB
    """
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")

    power = int(math.log(max(abs(byte), 1), 1024))

    return f"{byte / (1024 ** power):.2f} {units[power]}"


@Base.debug.subcommand(  # pyright: ignore[reportUnknownMemberType]
    name="info", inherit_hooks=True
)
async def debug_info(interaction: Interaction[BotT]):
    from . import __version__

    embed = Embed(colour=0x8000FF)

    embed.add_field(
        name="Versions",
        value=f"delarva: {__version__}\nnextcord: {nextcord.__version__}",
    )

    embed.add_field(
        name="Latency",
        value=f"Gateway: {interaction.client.latency * 1000:.2f}ms",
    )

    embed.add_field(name="Loaded", value=f"{format_dt(UP_TIME, style='R')}")

    embed.add_field(
        name="System Info",
        value=f"Python: {platform.python_version()} {platform.python_implementation()} "
        f"\nOS: {platform.system()}",
    )

    if psutil is not None:
        process = psutil.Process()
        memory = process.memory_full_info()
        embed.add_field(
            name="Memory Usage",
            value=f"Total: `{human_size(memory.rss)}`"
            f"\nVirtual: `{human_size(memory.vms)}`"
            f"\nProcess: `{human_size(memory.uss)}`",  # pyright: ignore[reportGeneralTypeIssues]
        )

        embed.add_field(
            name="Process Info",
            value=f"PID: {process.pid}\nThreads: {process.num_threads()}",
        )

    if isinstance(interaction.client, AutoShardedClient):
        if len(interaction.client.shards) > 25:
            shard_info = (
                f"Automatically sharded ({len(interaction.client.shards)} "
                f"shards of {interaction.client.shard_count})"
            )
        else:
            shard_ids = ", ".join(str(s) for s in interaction.client.shards.keys())
            shard_info = (
                f"Automatically sharded ({shard_ids} of"
                f" {interaction.client.shard_count})"
            )
    else:
        if interaction.client.shard_count is None:
            shard_info = "Not sharded"
        else:
            shard_info = f"Sharded ({interaction.client.shard_id} in {interaction.client.shard_count} shards)"

    embed.add_field(name="Sharding", value=shard_info)

    embed.add_field(
        name="Cache Counts",
        value=f"Guilds: {len(interaction.client.guilds)}\n"
        f"Users: {len(interaction.client.users)}",
    )

    intents = ", ".join(
        f"`{value}`" for value, enabled in interaction.client.intents if enabled
    )
    values = (
        value
        for value, enabled in interaction.client._connection.member_cache_flags  # pyright: ignore[reportPrivateUsage]
        if enabled
    )
    member_cache = ", ".join(f"`{v}`" for v in values)
    embed.add_field(
        name="Config",
        value=f"Intents: {intents}\nMember Cache: {member_cache}",
        inline=False,
    )

    await interaction.response.send_message(embed=embed)
