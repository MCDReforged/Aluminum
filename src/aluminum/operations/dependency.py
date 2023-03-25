from abc import ABC, abstractmethod
from enum import Enum

import pkg_resources
from mcdreforged.plugin.meta.version import VersionParsingError, VersionRequirement

from aluminum.constants import DEPENDENCY_BLACKLIST, psi


class DependencyCheckStatus(Enum):
    NOT_FOUND = 'dependency.status.not_found'
    INVALID = 'dependency.status.invalid'
    UNACCEPTED = 'dependency.status.unaccepted'
    SUCCESS = 'dependency.status.success'


class DependencyOperation(Enum):
    IGNORE = 'dependency.operation.ignore'
    INSTALL = 'dependency.operation.install'
    UPGRADE = 'dependency.operation.upgrade'


class Dependency(ABC):
    def __init__(self, name: str, requirement: str):
        self.name = name
        self.requirement = requirement

    @abstractmethod
    def check(self):
        raise NotImplementedError

    def get_operation(self) -> DependencyOperation:
        operations = {
            DependencyCheckStatus.NOT_FOUND: DependencyOperation.INSTALL,
            DependencyCheckStatus.UNACCEPTED: DependencyOperation.UPGRADE,
            DependencyCheckStatus.INVALID: DependencyOperation.IGNORE,
            DependencyCheckStatus.SUCCESS: DependencyOperation.IGNORE
        }
        return operations[self.check()]


class PackageDependency(Dependency):
    def __init__(self, name: str, requirement: str):
        super().__init__(name, requirement)

    def check(self):
        try:
            pkg_resources.require(self.requirement)
        except pkg_resources.DistributionNotFound:
            return DependencyCheckStatus.NOT_FOUND
        except pkg_resources.VersionConflict:
            return DependencyCheckStatus.UNACCEPTED


class PluginDependency(Dependency):
    def __init__(self, name: str, requirement: str):
        super().__init__(name, requirement)

    def _check_version(self, version: str):
        try:
            if not VersionRequirement(self.requirement).accept(version):
                return DependencyCheckStatus.UNACCEPTED
        except VersionParsingError:
            return DependencyCheckStatus.INVALID

    def check(self):
        if not is_plugin_loaded(self.name) and self.name not in DEPENDENCY_BLACKLIST:
            return DependencyCheckStatus.NOT_FOUND
        metadata = psi.get_plugin_metadata(self.name)
        self._check_version(metadata.version)
