from typing import Union
from mcdreforged import plugin

from mcdreforged.translation.translation_text import RTextMCDRTranslation
from aluminum.constant import trans
from colorama import Fore

class AluminumException(Exception):
    """Base exception for Aluminum."""

    def __init__(self, msg: Union[RTextMCDRTranslation, str], detail: str = ''):
        self.msg = Fore.LIGHTRED_EX + msg + Fore.RESET
        if detail:
            self.msg += f': {detail}'
    
    def __str__(self):
        return self.msg

class NetworkError(AluminumException):
    """Network error."""

    def __init__(self, file: str, detail: str):
        super().__init__(trans('aluminum.network_error', file), detail)

class PluginNotFoundError(AluminumException):
    """The target plugin does not exist."""

    def __init__(self, plugin_id: str):
        super().__init__(trans('aluminum.install.not_found', plugin_id))

class PluginAlreadyExistsError(AluminumException):
    """The target plugin is already exists."""

    def __init__(self, plugin_id: str):
        super().__init__(trans('aluminum.install.already_exists', plugin_id))

class NoAvailableAssetError(AluminumException):
    """The target plugin has no downloadable asset."""

    def __init__(self, plugin_id: str):
        super().__init__(trans('aluminum.install.no_release', plugin_id))

class SeesionLockError(AluminumException):
    """Another seesion is running."""

    def __init__(self):
        super().__init__(trans('aluminum.install.lock'))

class DependenciesInstallError(AluminumException):
    """Error while installing dependencies."""

    def __init__(self, dependence, detail):
        super().__init__(trans('aluminum.install.dep_error', dependence, detail))

class RequirementInstallError(AluminumException):
    """Error while installing requirements."""

    def __init__(self, requirement, detail):
        super().__init__(trans('aluminum.install.pip_error', requirement, detail))