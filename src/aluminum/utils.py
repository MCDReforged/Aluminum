import re
import shutil
import subprocess
from threading import Thread
import time
import pkg_resources
from sys import executable as python
from typing import Callable, List, Tuple

import requests
from mcdreforged.api.all import *
from mcdreforged.plugin import plugin_factory
from mcdreforged.utils import file_util

from aluminum.constant import *
from aluminum.exceptions import NetworkError, RequirementInstallError

class AluminumClock(Thread):
    def __init__(self, interval: int, event: Callable) -> None:
        super().__init__()
        self.setDaemon(True)
        self.setName(self.__class__.__name__)
        self.interval = interval
        self.event = event
    
    def run(self):
        while True:
            time.sleep(self.interval)
            self.event()



def download_file(file_url: str, name: str):
    """Download a file from the Internet.

    Args:
        file_url (str): The URL of target file.
        name (str): The path to save the file.
    """

    try:
        logger.info(trans('aluminum.install.downloading', name))
        path = os.path.join(PLUGIN_FOLDER, name)
        r = requests.get(file_url, stream=True)
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    except requests.RequestException as e:
        raise NetworkError(name, e)


def get_unloaded_plugins() -> List[str]:
    """Return a list of unloaded (not disabled) plugins."""
    def get_files_in_plugin_directories(filter: Callable[[str], bool]) -> List[str]:
        result = []
        for plugin_directory in global_server.get_mcdr_config()['plugin_directories']:
            result.extend(file_util.list_all(plugin_directory, filter))
        return result

    mcdr_server = global_server._mcdr_server()
    # type: List[str]
    return get_files_in_plugin_directories(lambda fp: plugin_factory.maybe_plugin(fp) and not mcdr_server.plugin_manager.contains_plugin_file(fp))


def pip_install(module: str):
    try:
        try:
            pkg_resources.require(module)
        except pkg_resources.DistributionNotFound:
            logger.info(trans('aluminum.install.install_pip', module))
            subprocess.check_call([python, '-m', 'pip', '--disable-pip-version-check', 'install', module, '-q'])
        else:
            logger.info(trans('aluminum.install.pip_installed', module))
    except subprocess.CalledProcessError as e:
        raise RequirementInstallError(module, e)



@new_thread(PLUGIN_ID)
def with_new_thread(func: Callable, *args, **kwargs):
    """Run function in a new thread.

    Args:
        func (Callable): The function to run.
    """
    func(*args, **kwargs)


def split_plugin_name(text: str) -> Tuple[str, VersionRequirement]:
    """Split plugin name with version requirement.

    Examples:
        mcdreforged>=0.1.0 -> ('mcdreforged', '>=0.1.0')
    """
    match = re.match(SEMVER_PATTERN, text).groups()
    plugin_id = match[0]
    version = match[1] if match[1] else '*'
    return (plugin_id, version)


def clear_line():
    """Print a blank line as split line (?)"""
    print('\n')
