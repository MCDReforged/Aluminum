from typing import Optional, Any

from mcdreforged.api.rtext import RColor, RText, RTextBase
from mcdreforged.api.types import CommandSource

from aluminum.constants import PLUGIN_ID, psi


def console_print(msg):
    for line in RTextBase.from_any(msg).to_colored_text().splitlines():
        psi.logger.info(line)


def print_msg(src: Optional[CommandSource], msg, color: RColor = None, console=True):
    if src:
        if color:
            msg = RText(msg, color)
        if src.is_player:
            src.reply(msg)
        if console:
            console_print(msg)


def tn(name) -> str:
    """Generate a thread name.
    """
    return f'{PLUGIN_ID}-{name}'


def is_integer(text):
    try:
        int(text)
        return True
    except:
        return False
