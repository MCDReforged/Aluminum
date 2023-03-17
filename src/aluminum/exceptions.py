class AluminumException(Exception):
    """Base exception for Aluminum."""
    pass


class NetworkError(AluminumException):
    """Network error."""
    pass


class CatalogueUpdateError(AluminumException):
    """Failed to update plugin catalogue."""
    pass


class CorruptedOnlineMetaError(AluminumException):
    """Broken meta zip file."""
    pass


class CatalogueLoadError(AluminumException):
    """Failed to load local cache."""
    pass


class SessionLockError(AluminumException):
    """Another seesion is running."""
    pass


class DependencyInstallError(AluminumException):
    """Error while installing dependencies."""
    pass


class RequirementInstallError(AluminumException):
    """Error while installing requirements."""
    pass


class PluginFolderError(AluminumException):
    """Plugin folder not found in MCDR config."""
    pass

class SpecialRequirementError(AluminumException):
    """A requirement provided a semver like version specifiers."""
    pass
