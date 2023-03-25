from typing import Dict, List, Optional, Type, Union
from aluminum.utils.type import PrettySerializable
from mcdreforged.utils.serializer import deserialize

class Asset(PrettySerializable):
    name: str
    browser_download_url: str


class Release(PrettySerializable):
    """
    A release of certain plugin.
    """
    url: Optional[str]
    assets: List[Asset]
    parsed_version: str
    dependencies: Dict[str, str]
    requirements: List[str]

    @property
    def validate(self):
        return type(self.meta) == PluginMeta and self.assets
    
    @classmethod
    def load(cls: 'Release', data: dict, **kwargs) -> 'Release':
        result =  cls.deserialize(data, cls, **kwargs)
        result.dependencies = data['meta']['dependencies']
        result.requirements = data['meta']['requirements']
        return result


class ReleaseSummary(PrettySerializable):
    schema_version: int = None
    id: str
    latest_version: str
    etag: str = ''
    releases: List[Release]

    def get_latest_release(self) -> Optional[Release]:
        if len(self.releases) > 0:
            return self.releases[0]
        return None


class PluginMeta(PrettySerializable):
    id: str
    name: str
    version: str
    repository: str
    labels: List[str]
    authors: List[Union[str, Dict[str, str]]]
    description: Dict[str, str]
    release_summary: ReleaseSummary

    @classmethod
    def of(cls: 'PluginMeta', meta_json: dict, plugin_json: dict, release_json: dict):
        meta_json.update(plugin_json)
        result = cls.deserialize(meta_json)
        result.release_summary = ReleaseSummary.deserialize(release_json)
        return result


# class Plugin(PrettySerializable):
#     """
#     A single MCDR plugin.
#     """

#     def __init__(self, plugin_json: dict, releases_json: list, meta: dict) -> None:
#         self.meta: PluginMeta = PluginMeta().deserialize(meta)
#         self.meta.labels = plugin_json['labels']
#         self.releases: List[Release] = []
#         self.latest: Version = None

#         latest = releases_json['latest_version']
#         self.latest = Version(latest) if latest != 'N/A' else N_INF
#         releases = releases_json['releases']
#         if releases:
#             for i in releases:
#                 release = Release.deserialize(i)
#                 if release.validate:
#                     self.releases.append(release)

#     def get_info_rtext(self, compared=None):
#         name_rtext = RText(self.meta.name, RColor.yellow, RStyle.bold)
#         self_version = Version(self.meta.version)
#         version_rtext = RText(self_version, RColor.green)
#         title_rtext = RTextList(name_rtext, ' ', version_rtext)
#         if compared:
#             compared_rtext = RText(f" §7[{utils.trans('Installed')} {compared.version}]" if compared.version <
#                                    self_version else f" §7[{utils.trans('Installed')}]", RColor.gray)
#             title_rtext.append(compared_rtext)
#         title_rtext.append('\n')

#         info_rtext = RTextList(title_rtext,
#                                RTextList(utils.trans('ID: {}', self.meta.id), '\n'),
#                                RTextList(utils.trans('Author: {}', ', '.join(self.meta.authors)), '\n'),
#                                RTextBase.format(utils.trans('Link: {}'), RText(self.meta.repository, RColor.blue,
#                                                 RStyle.underlined).c(RAction.open_url, self.meta.repository)), '\n',
#                                self.meta.description
#                                if type(self.meta.description) == str
#                                # !
#                                else self.meta.description.get(psi.get_mcdr_language(), self.meta.description.get('en_us', None))
#                                )
#         return info_rtext

#     def get_release(self, requirement: Union[VersionRequirement, str] = '*') -> List[Release]:
#         """Get latest release that matches the version requirement.

#         Args:
#             requirement (Union[VersionRequirement, str], optional): Version requiirement. Defaults to '*'.

#         Returns:
#             Release: Latest matched release.
#         """
#         matched_releases = [r for r in self.releases if requirement.accept(r.meta.version)]
#         return max(matched_releases, key=lambda r: r.meta.version)

#     def search(self, keyword: str):
#         return self.meta.search(keyword)
