import os
import sched
import threading
import time
import zipfile
from typing import Any, Callable, List, Optional, Tuple

import requests
from mcdreforged.api.decorator import new_thread
from mcdreforged.api.rtext import RColor, RText, RTextBase
from mcdreforged.api.types import CommandSource
from mcdreforged.utils.serializer import Serializable

from aluminum.constant import PLUGIN_ID, global_server, TRANSLATION
from aluminum.exceptions import CorruptedOnlineMetaError, NetworkError


class ValueDict(dict):
    def __iter__(self):
        return iter(self.values())


class PrettySerializable(Serializable):
    def __repr__(self) -> str:
        return represent(self)


import threading

class TaskScheduler:
    """
    A class that encapsulates a scheduler and allows you to add one-time and interval tasks,
    cancel tasks, and stop the scheduler.
    """

    def __init__(self, interval: int, target: callable, thread_name="TaskScheduler", arguments: tuple = ()):
        """
        Initialize the scheduler with a specified thread name.
        """
        self.thread_name = thread_name
        self.target = target
        self.interval = interval
        self.arguments = arguments
        self.tasks = {}
        self.lock = threading.Lock()
    
    def start(self):
        self.target(*self.arguments)
        self.timer = threading.Timer(self.interval, self.start)
        self.timer.setName(self.thread_name)
        self.timer.start()
    
    def stop(self):
        self.timer.cancel()


def check_lock(func):
    """
    Decorator to wrap a function to ensure that the function is executed under the session lock.
    """
    def wrapper(s, source, *args, **kwargs):
        if s.lock.locked():
            print_msg(source, trans('§cSeesion in use.'))
            return None
        with s.lock:
            return func(s, source, *args, **kwargs)
    return wrapper


def console_print(msg):
    for line in RTextBase.from_any(msg).to_colored_text().splitlines():
        global_server.logger.info(line)


def print_msg(src: Optional[CommandSource], msg, color: RColor = None, console=True):
    if src:
        if color:
            msg = RText(msg, color)
        if src.is_player:
            src.reply(msg)
        if console:
            console_print(msg)


def trans(msg, *args):
    if global_server.get_mcdr_language() == 'zh_cn':
        try:
            msg = TRANSLATION[msg]
        except:
            msg = f'[未译: {msg}]'
    if args:
        msg = msg.format(*args)
    return msg


def download_file(file_url: str, name: str, path: str):
    """Download a file from the Internet.

    Args:
        file_url (str): The URL of target file.
        name (str): The path to save the file.
    """

    try:
        path = os.path.join(path, name)
        r = requests.get(file_url, stream=True)
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    except requests.RequestException as e:
        raise NetworkError(e)


def unzip(file, path):
    try:
        with zipfile.ZipFile(file) as zip:
            if zip.testzip():
                raise CorruptedOnlineMetaError(f'File {file} is broken')
            zip.extractall(path)
    except Exception as e:
        raise CorruptedOnlineMetaError(e)


def touch(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def represent(obj: Any) -> str:
    """
    aka repr
    """
    return '{}[{}]'.format(type(obj).__name__, ','.join([
        '{}={}'.format(k, repr(v)) for k, v in vars(obj).items() if not k.startswith('_')
    ]))


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
