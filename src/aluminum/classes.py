import json
import os
import re
import sched
import subprocess
from threading import Lock
import time
from typing import Dict, List, Optional, Union

import pkg_resources
from mcdreforged.api.decorator import new_thread
from mcdreforged.api.rtext import RColor, RText, RAction, RStyle, RTextBase, RTextList
from mcdreforged.api.types import CommandSource, Metadata, Version, VersionRequirement

import aluminum.utils as utils
from aluminum.constant import PLUGIN_CATALOGUE, PLUGIN_FOLDER, PYTHON, Configuration, global_server, PREFIX, N_INF, DEPENDENCY_BLACKLIST
from aluminum.decorator import execute_on_second_time
from aluminum.exceptions import CatalogueLoadError, CatalogueUpdateError, DependencyInstallError, RequirementInstallError, PluginFolderError, SpecialRequirementError
from aluminum.utils import PrettySerializable, ValueDict


class Dependency:
    id: str
    version_requirement: VersionRequirement

    def __init__(self, dependency_spec, version_requirement: Optional[Union[str, VersionRequirement]] = None) -> None:
        if version_requirement:
            self.id = dependency_spec
            self.version_requirement = VersionRequirement(version_requirement)
        else:
            pattern = r'^(?P<id>[\w\-]+)(?P<version_requirement>.*)$'
            match = re.match(pattern, dependency_spec)
            if match:
                self.id = match.group('id')
                version_requirement = match.group('version_requirement') or '*'
                self.version_requirement = VersionRequirement(version_requirement)
            else:
                raise ValueError(f'Invalid dependency specification: {dependency_spec}')

    def __repr__(self):
        return f'{self.id}{self.version_requirement}'


class PluginMeta(PrettySerializable):
    id: str = ''
    name: str = ''
    version: str = ''
    repository: str = ''
    labels: List[str] = []
    authors: List[Union[str, Dict[str, str]]] = []
    dependencies: Dict[str, str] = {}
    requirements: list = []
    description: Union[Dict[str, str], str] = ''

    def search(self, keyword: str) -> bool:
        if keyword.lower() in self.id.lower():
            return True
        if keyword.lower() in self.name.lower():
            return True
        if isinstance(self.description, dict):
            for _, desc in self.description.items():
                if keyword.lower() in desc.lower():
                    return True
        elif isinstance(self.description, str):
            if keyword.lower() in self.description.lower():
                return True
        return False


class Asset(PrettySerializable):
    name: str
    download_count: int
    browser_download_url: str


class Release(PrettySerializable):
    """
    A release of certain plugin.
    """
    url: Optional[str] = None
    created_at: str
    assets: List[Asset]
    parsed_version: str = None
    meta: Union[PluginMeta, str]

    @property
    def validate(self):
        return type(self.meta) == PluginMeta and self.assets


class Plugin(PrettySerializable):
    """
    A single MCDR plugin.
    """

    def __init__(self, plugin_json: dict, releases_json: list, meta: dict) -> None:
        self.meta: PluginMeta = PluginMeta().deserialize(meta)
        self.meta.labels = plugin_json['labels']
        self.releases: List[Release] = []
        self.latest: Version = None

        latest = releases_json['latest_version']
        self.latest = Version(latest) if latest != 'N/A' else N_INF
        releases = releases_json['releases']
        if releases:
            for i in releases:
                release = Release.deserialize(i)
                if release.validate:
                    self.releases.append(release)

    def get_info_rtext(self, compared=None):
        name_rtext = RText(self.meta.name, RColor.yellow, RStyle.bold)
        self_version = Version(self.meta.version)
        version_rtext = RText(self_version, RColor.green)
        title_rtext = RTextList(name_rtext, ' ', version_rtext)
        if compared:
            compared_rtext = RText(f" §7[{utils.trans('Installed')} {compared.version}]" if compared.version <
                                   self_version else f" §7[{utils.trans('Installed')}]", RColor.gray)
            title_rtext.append(compared_rtext)
        title_rtext.append('\n')

        info_rtext = RTextList(title_rtext,
                               RTextList(utils.trans('ID: {}', self.meta.id), '\n'),
                               RTextList(utils.trans('Author: {}', ', '.join(self.meta.authors)), '\n'),
                               RTextBase.format(utils.trans('Link: {}'), RText(self.meta.repository, RColor.blue,
                                                RStyle.underlined).c(RAction.open_url, self.meta.repository)), '\n',
                               self.meta.description
                               if type(self.meta.description) == str
                               # !
                               else self.meta.description.get(global_server.get_mcdr_language(), self.meta.description.get('en_us', None))
                               )
        return info_rtext

    def get_release(self, requirement: Union[VersionRequirement, str] = '*') -> List[Release]:
        """Get latest release that matches the version requirement.

        Args:
            requirement (Union[VersionRequirement, str], optional): Version requiirement. Defaults to '*'.

        Returns:
            Release: Latest matched release.
        """
        matched_releases = [r for r in self.releases if requirement.accept(r.meta.version)]
        return max(matched_releases, key=lambda r: r.meta.version)

    def search(self, keyword: str):
        return self.meta.search(keyword)


class PluginCatalogue:
    plugins: ValueDict[str, Plugin]

    def __init__(self, data_folder: str, config: Configuration, lock: Lock) -> None:
        self.config = config
        self.data_folder = data_folder
        self.cache_folder = utils.touch(os.path.join(data_folder, 'cache'))
        self.plugins = ValueDict()
        self._last_check = 0
        self.lock = lock
        self.load(True)

    @property
    def last_check(self):
        if not self._last_check:
            try:
                with open(os.path.join(self.cache_folder, 'last_update'), 'r', encoding='utf8') as f:
                    self._last_check = float(f.read())
            except:
                pass
        return self._last_check

    @utils.check_lock
    def _update(self, src=global_server.get_plugin_command_source()) -> None:
        """
        Update Plugin Catalogue.
        """
        src.reply(utils.trans('Updating catalogue...'))
        try:
            utils.download_file(self.config.source, 'meta.zip', self.cache_folder)
            zip = os.path.join(self.cache_folder, 'meta.zip')
            utils.unzip(zip, self.cache_folder)  # !
        except Exception as e:
            utils.print_msg(src, utils.trans('Catalogue update failed: {}', e), RColor.red, console=False)
            raise CatalogueUpdateError(e)
        else:
            os.remove(zip)
            utils.print_msg(src, utils.trans('Catalogue update §asucceed'))
            self._last_check = time.time()
            with open(os.path.join(self.cache_folder, 'last_update'), 'w', encoding='utf8') as f:
                f.write(str(self._last_check))
        finally:
            self.load()

    @new_thread(utils.tn('Update'))
    def update(self, *args):
        self._update(*args)

    def load(self, pass_exception: bool = False) -> None:
        try:
            meta_folder = os.path.join(self.cache_folder, 'PluginCatalogue-meta')
            for subdir, _, _ in os.walk(meta_folder):
                if subdir != meta_folder:
                    with open(os.path.join(subdir, 'plugin.json'), 'r', encoding='utf8') as f:
                        plugin_json = json.load(f)
                    with open(os.path.join(subdir, 'release.json'), 'r', encoding='utf8') as f:
                        release_json = json.load(f)
                    with open(os.path.join(subdir, 'meta.json'), 'r', encoding='utf8') as f:
                        meta_json = json.load(f)
                    self.plugins[meta_json['id']] = Plugin(plugin_json, release_json, meta_json)
        except Exception as e:
            if not pass_exception:
                raise CatalogueLoadError(e)

    def filter(self, sort_by: str = 'name', label: Optional[str] = None, plugin_list: List[str] = None, keyword: str = None) -> List[Plugin]:
        """Get filtered plugins.

        Args:
            sort_by (str): labels / name / authors

        Raises:
            ValueError: When sort_by isn't a validate sort method.

        Returns:
            List[Plugin]
        """
        plugins = self.plugins
        if keyword:
            plugins = [p for p in self.plugins if p.search(keyword)]
        if plugin_list:
            plugins = [p for p in self.plugins if p.meta.id in plugin_list]
        if label:
            plugins = [p for p in self.plugins if label in p.meta.labels]
        if sort_by not in ['labels', 'name', 'authors']:
            raise ValueError(utils.trans('Can\'t sort by {}', sort_by))
        return sorted(plugins, key=lambda p: eval(f'p.meta.{sort_by}'))

    def get(self, plugin_id, default=None) -> Plugin:
        return self.plugins.get(plugin_id, default)

    def get_release(self, dependency: Dependency) -> Union[Release, None]:
        """
        Get latest matched release from catalogue.
        """
        plugin = self.get(dependency.id)
        if plugin:
            return plugin.get_release(dependency.version_requirement)
        raise LookupError(utils.trans('No available release for "§e{}§r"', dependency))


class PluginManager:
    catalogue: PluginCatalogue
    _plugins: ValueDict[Metadata]

    def __init__(self, config: Configuration, lock: Lock) -> None:
        if config.plugin_folder not in global_server.get_mcdr_config()['plugin_directories']:
            raise PluginFolderError(utils.trans('{} is not a MCDR plugin dictionary', config.plugin_folder))
        self.config = config
        self._plugins = ValueDict(global_server.get_all_metadata())
        self.catalogue = PluginCatalogue(global_server.get_data_folder(), config, lock)
        self.lock = lock
        self.scheduler = utils.TaskScheduler(config.update_interval, self.check_update,
                                             utils.tn('AutoUpdate'),
                                             arguments=(global_server.get_plugin_command_source(), True,))
        self.scheduler.start()
        # self.check_update(global_server.get_plugin_command_source())

    def update(self):
        self._plugins = ValueDict(global_server.get_all_metadata())

    @property
    def outdated_plugins(self) -> List[str]:
        return self._check_upgrade(None)

    def _check_upgrade(self, src=None) -> List[str]:
        outdated_plugins = []
        for plugin in self.plugins:
            plugin: Metadata
            online_plugin = self.catalogue.get(plugin.id, None)
            if online_plugin:
                if online_plugin.latest > plugin.version:
                    outdated_plugins.append(plugin.id)
        if outdated_plugins:
            command = f'{PREFIX[0]} browse outdated'
            utils.print_msg(src, RTextBase.format(utils.trans('§e{} outdated plugins§r detected. Use §3{} §rfor more infimation.'), str(
                len(outdated_plugins)), RText(command, RColor.aqua, RStyle.bold).c(RAction.run_command, command)))
        else:
            utils.print_msg(src, utils.trans('Your plugins are all latest!'), RColor.green)
        return outdated_plugins

    @utils.check_lock
    @new_thread(utils.tn('UpgradeCheck'))
    def check_upgrade(self, src=None):
        self._check_upgrade(src)

    @utils.check_lock
    @new_thread(utils.tn('UpdateCheck'))
    def check_update(self, src: CommandSource, is_autoupdate: bool = False, check_upgrade: bool = None):
        if check_upgrade is None:
            check_upgrade = self.config.check_upgrade
        if is_autoupdate:
            utils.print_msg(src, utils.trans('Automatic catalogue update started'))
        if time.time() - self.catalogue.last_check >= self.config.update_interval:
            #! TODO: refactor to PluginCatalogue, take class Session out alone
            self.catalogue._update(src)
        if check_upgrade:
            self._check_upgrade(src)

    @property
    def plugins(self) -> ValueDict[Metadata]:
        self.update()
        return self._plugins

    def requires(self, dependency: Dependency):
        plugin: Metadata = self.plugins.get(dependency.id)
        if plugin:
            if dependency.version_requirement.accept(plugin.version):
                return True
        return False

    def __pip_install(self, src, module):
        try:
            try:
                pkg_resources.require(module)
                if re.match(r'^(\w+)', module).group(1) not in DEPENDENCY_BLACKLIST:
                    utils.print_msg(src, utils.trans('Requirement "§e{}§r" §aalready satisfied', module))
            except (pkg_resources.DistributionNotFound):
                utils.print_msg(src, utils.trans('Installing requirement "§e{}§r"', module))
                subprocess.check_call([PYTHON, '-m', 'pip',
                                      '--disable-pip-version-check', 'install', module, '-q'])
                utils.print_msg(src, utils.trans('Module "§6{}§r" §linstalled§r §asuccessfully§r', module))
            except pkg_resources.VersionConflict:
                utils.print_msg(src, utils.trans(
                    'Detected version conflict of required module {}. Please resolve it yourself to prevent errors with other plugins.', module))
                raise
        except Exception as e:
            raise RequirementInstallError(e)

    def __perform_install(self, src: CommandSource, dependency: Dependency, release: Release, is_dependency: Optional[bool] = False, is_upgrade: Optional[bool] = False, plugin_folder: Optional[str] = PLUGIN_FOLDER):
        """Install a plugin from catalogue.

        Args:
            dependency_spec (str): `plugin_id>=1.0.0` or `plugin_id` for example.
            is_dependency (bool, optional): Install as a dependency for another plugin. Defaults to False.
        """
        #! Todo: Multi plugins install
        try:
            action = utils.trans('§lUpgrading§r') if is_upgrade else utils.trans('§lInstalling§r')
            item = utils.trans('dependency') if is_dependency else utils.trans('plugin')
            msg = f'{action} {item}: "§e{dependency}§r"'
            utils.print_msg(src, msg)

            dependencies = release.meta.dependencies
            for d in dependencies:
                try:
                    self._install(src, d, dependencies[d], is_dependency=True, install_method=self.__perform_install)
                except Exception as e:
                    raise DependencyInstallError(e)
            for r in release.meta.requirements:
                self.__pip_install(src, r)

            if len(release.assets) > 1:
                #! TODO: support multi assets
                pass
            asset = release.assets[0]
            utils.download_file(asset.browser_download_url, asset.name, plugin_folder)
            #! TODO: support ghproxy, fastgit, etc.

            if is_upgrade:
                self._disable(dependency.id)

            if global_server.load_plugin(os.path.join(plugin_folder, asset.name)):
                utils.print_msg(src, utils.trans('Plugin "§e{}@{}§r" §linstalled§r §asuccessfully§r',
                                dependency.id, release.meta.version))
        except DependencyInstallError as e:
            error = utils.trans('§cFail§r to §linstall§r dependency §e{}§r', dependency)
            utils.print_msg(src, f"{error}: {e}", RColor.red, False)
            raise  # ! TODO: logger.debug instead of raise
        except RequirementInstallError as e:
            error = utils.trans('§cFail§r to §linstall§r requirement §6{}§r', dependency)
            utils.print_msg(src, f"{error}: {e}", RColor.red, False)
            raise
        except Exception as e:
            error = utils.trans('§cFail§r to §linstall§r {}', dependency if dependency else dependency)
            utils.print_msg(src, f"{error}: {e}", RColor.red, False)
            raise

    @execute_on_second_time(10, utils.trans('installing or upgrading'), f'{PREFIX[0]} install {{}}')
    def __confirm_and_install(self, *a, **kw):
        self.__perform_install(*a, **kw)

    def _install(self, src: CommandSource, dependency_spec: str, version_requirement: Optional[Union[str, VersionRequirement]] = None, is_dependency: Optional[bool] = False, plugin_folder: Optional[str] = PLUGIN_FOLDER, install_method: callable = __perform_install):
        try:
            dependency = Dependency(dependency_spec, version_requirement)
            if dependency.id in DEPENDENCY_BLACKLIST:
                if not self.requires(dependency):
                    raise SpecialRequirementError(utils.trans(
                        '§cAluminum can\'t install §6{}§c automatically. You may install it yourself.'), dependency)
                return
            else:
                if self.requires(dependency) and dependency.id not in list(self.outdated_plugins):
                    utils.print_msg(src, utils.trans('Dependency "§e{}§r" §aalready satisfied', dependency))
                    return

            is_upgrade = dependency.id in self.plugins
            release = self.catalogue.get_release(dependency)
        except Exception as e:
            utils.print_msg(src, f'§c{e}')
            raise  # !
        else:
            install_method(src, dependency, release, is_dependency, is_upgrade, plugin_folder)

    @new_thread(utils.tn('Install'))
    @utils.check_lock
    def install(self, *args, **kwargs):
        self._install(*args, **kwargs, install_method=self.__confirm_and_install)

    def _disable(self, plugin_id):
        path = global_server.get_plugin_file_path(plugin_id)
        try:
            return global_server.disable_plugin(plugin_id)
        except FileExistsError:
            pass
        return path

    @utils.check_lock
    def disable(self, src: CommandSource, plugin_id):
        plugin = self.plugins.get(plugin_id, None)
        if not plugin:
            src.reply(utils.trans('Invalid plugin id "§e{}§r"', plugin_id))
            return
        self._disable(plugin_id)
        src.reply(utils.trans('Disable "§e{}@{}§r" §asuccessfully', plugin_id, plugin.version))

    def generate_rtext(self, src: CommandSource, local: Metadata, plugin: Plugin = None, language: str = 'en_us'):
        def get_button(label, value, hover, url=False):
            return RText(f'§l{label}§r'). \
                c(RAction.open_url if url else RAction.run_command, value if url else f'{PREFIX[0]} {value} {meta.id}'). \
                h(utils.trans(hover))

        author = next(iter(plugin.meta.authors if plugin else local.author))
        meta = plugin.meta if plugin else local

        name_and_version = RTextList(
            RText(f'§6{author}/§e{meta.name}'), ' ',
            RText(f'§a{meta.version}')
        )

        info = get_button('§l§3≡§r', 'info', '§3Show detailed infomation')
        install = get_button('§l§a↓§r', 'install', '§aInstall')
        uninstall = get_button('§l§c×§r', 'disable', '§cDisable')
        reload = get_button('§l§6⟳§r', 'reload', '§6Reload')
        website = get_button('§l§a☁§r', meta.link if hasattr(meta, 'link') else meta.repository, '§aOpen website', True)
        updgrade = get_button('§l§6↑§r', 'install', '§6Upgrade')

        if not local:
            installed = ''
            button = RTextList(install, '·', website, '·',  info)
        elif plugin.latest > local.version:
            installed = RText(f" §7[{utils.trans('Installed')} {local.version}]")
            button = RTextList(updgrade, '·', uninstall, '·', info)
        else:
            installed = RText(f" §7[{utils.trans('Installed')}]")
            button = RTextList(uninstall, '·', reload, '·', info)

        desc = meta.description \
            if type(meta.description) == str \
            else meta.description.get(language, meta.description.get('en_us', None))
        desc = RText(desc) if desc else RText(utils.trans('No description provided.'), RColor.gray, RStyle.italic)
        desc = RTextList(' '*6 if src.is_player else ' '*3, desc)

        if src.is_player:
            return RTextList('[', button, '] ', name_and_version, installed, '\n', desc)
        else:
            return RTextList(name_and_version, installed, '\n', desc)

    def filter(self, index: str, sort_by: str = 'name', page: int = None, page_size: int = None, keyword: str = None) -> List[Plugin]:
        def get_page(lst, page, page_size):
            if not page_size:
                return lst
            start = (page - 1) * page_size
            end = start + page_size
            return lst[start:end]
        if index == 'outdated':
            outdated_plugins = self.outdated_plugins
            plugins = self.catalogue.filter(sort_by, plugin_list=outdated_plugins, keyword=keyword)
        elif index == 'all':
            plugins = self.catalogue.filter(sort_by, keyword=keyword)
        elif index == 'installed':
            plugins = self.catalogue.filter(sort_by, plugin_list=self.plugins.keys(), keyword=keyword)
        else:
            plugins = self.catalogue.filter(sort_by, label=index, keyword=keyword)
        if page:
            return get_page(plugins, page, page_size)
        return plugins

    def max_page(self, index: str, page_size: int, keyword: str = None):
        plugins = self.filter(index, keyword=keyword)
        return (len(plugins) + page_size - 1) // page_size

    def browse(self, src: CommandSource, index: str, sort_by: str = 'name', page: int = 1, page_size: int = None, keyword: str = None):
        if index == 'outdated' and not self.outdated_plugins:
            src.reply(RText(utils.trans('Your plugins are all latest!'), RColor.green))
            return
        plugins = self.filter(index, sort_by, page, page_size, keyword=keyword)
        for p in plugins:
            src.reply(self.generate_rtext(src, self.plugins.get(p.meta.id, None), p, src.get_preference().language))
        if page_size:
            max_page = self.max_page(index, page_size, keyword)
            if max_page > 1:
                page_menu = RTextList('§7[ ')
                if keyword:
                    command = f'{PREFIX[0]} search {keyword} {{}}'
                else:
                    command = f'{PREFIX[0]} browse {index} {sort_by} {{}}'
                for p in range(1, max_page + 1):
                    if p == page:
                        page_menu.append(RText(f'{p}', RColor.dark_green, (RStyle.bold, RStyle.underlined))).append(' ')
                    else:
                        page_menu.append(RText(f'{p}', RColor.gray).c(
                            RAction.run_command, command.format(p))).append(' ')
                page_menu.append('§7]')
                src.reply(page_menu)

    def info(self, src: CommandSource, plugin_id: str):
        if plugin_id in self.catalogue.plugins:
            src.reply(self.catalogue.plugins[plugin_id].get_info_rtext(self.plugins.get(plugin_id, None)))
        else:
            src.reply(self.plugins[plugin_id].get_info_rtext())
