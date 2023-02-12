# SPDX-License-Identifier: MIT
# pyright: reportImportCycles=false
from __future__ import annotations

import ast
from traceback import format_exception
from types import TracebackType
from typing import Any

from nextcord import Interaction, TextInputStyle, utils
from nextcord.ui import Modal, TextInput

from .base import Base, BotT


class CodeModal(Modal):
    def __init__(self):
        super().__init__("Evaluate Code")
        self.code = TextInput(  # pyright: ignore[reportUnknownMemberType]
            label="Code", style=TextInputStyle.paragraph
        )
        self.add_item(self.code)  # pyright: ignore[reportUnknownMemberType]
        self.interaction: Interaction[BotT] | None = None

    async def callback(self, interaction: Interaction[BotT]):
        self.interaction = interaction
        self.stop()


FMT = """
async def _eval_coroutine():
    import asyncio

    import nextcord
    import aiohttp
    from nextcord.ext import commands

    try:
        pass
    except Exception:
        pass
"""


def wrap_code(code: str) -> ast.Module:
    module = ast.parse(FMT)
    code_module = ast.parse(code)

    for node in ast.walk(module):
        node.lineno = -100_000
        node.end_lineno = -100_000

    func = module.body[-1]
    assert isinstance(func, ast.AsyncFunctionDef)

    try_block = func.body[-1]
    assert isinstance(try_block, ast.Try)

    try_block.body.extend(code_module.body)

    return module


class CatchErrors:
    def __init__(self, interaction: Interaction[BotT], ephemeral: bool):
        self.interaction = interaction
        self.ephemeral = ephemeral

    async def __aenter__(self):
        pass

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ):
        if exc is not None:
            await self.interaction.followup.send(
                f"```py\n{format_exception(exc_type, exc, tb)}\n```",
                ephemeral=self.ephemeral,
            )


@Base.debug.subcommand(name="eval")  # pyright: ignore[reportUnknownMemberType]
async def debug_eval(interaction: Interaction[BotT], ephemeral: bool = False):  # type: ignore
    """Evaluate some code.

    ephemeral:
        Whether or not to send the result as an ephemeral message.
    """
    modal = CodeModal()
    await interaction.response.send_modal(modal)
    await modal.wait()

    code = modal.code.value  # pyright: ignore[reportUnknownMemberType]
    modal_interaction = modal.interaction
    assert modal_interaction is not None
    assert code is not None

    localns: dict[str, Any] = {}
    globalns: dict[str, Any] = {
        "interaction": interaction,
        "guild": interaction.guild,
        "channel": interaction.channel,
        "user": interaction.user,
        "bot": interaction.client,
        "client": interaction.client,
        "get": utils.get,
        "find": utils.find,
    }
    exec(compile(wrap_code(code), "<eval>", "exec"), globalns, localns)
    func = localns.get("_eval_coroutine") or globalns["_eval_coroutine"]

    async with CatchErrors(modal_interaction, ephemeral=ephemeral):
        result = await func()

    await modal_interaction.followup.send(result or "No content.", ephemeral=ephemeral)
