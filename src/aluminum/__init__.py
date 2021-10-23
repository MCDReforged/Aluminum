import shutil
import time
import webbrowser
from urllib.parse import urljoin

import requests
from mcdreforged.api.all import *

from aluminum.constant import *
from aluminum.exceptions import *
from aluminum.utils import *

cache: dict = {}
need_update: List[str] = []
# seesion_lock: bool = False


@new_thread(PLUGIN_ID)
def install_from_string(plugin_string):
    plugin_string = split_plugin_name(plugin_string)
    plugin_id = plugin_string[0]
    version_requirement = VersionRequirement(plugin_string[1])
    install_plugin(plugin_id, version_requirement)


def install_plugin(plugin_id: str, version_requirement: Union[VersionRequirement, str] = VersionRequirement('*'), is_dependence: bool = False, is_update: bool = False):
    """Install a mcdreforged plugin."""

    def plugin_meta_url(plugin_id):
        return urljoin(META_CDN, PLUGIN_RELEASE_PATH.format(plugin_id))

    def get_target_asset():
        """Get asset by plugin id and version requirement."""

        releases = requests.get(plugin_meta_url(plugin_id)).json()['releases']
        target_release = None
        for i in releases:
            if version_requirement.accept(i['parsed_version']) and i['assets']:  # Check if accepted and downloadable
                target_release = i
                break

        if not target_release:
            raise NoAvailableAssetError(plugin_id)

        # TODO: Check if the plugin has more than one asset
        assets = target_release['assets']
        target_asset = assets[0]

        return target_asset

    try:
        # clear_line()

        if type(version_requirement) != VersionRequirement:  # Handle string
            version_requirement = VersionRequirement(version_requirement)

        if time.time() - cache['last_refresh'] >= config.cache_timeout:  # Refresh cache if timed out
            refresh_cache(global_server)

        plugins = cache['plugins']
        if plugin_id not in plugins:  # If not avaliable in plugin calalogue
            raise PluginNotFoundError(plugin_id)

        if plugin_id in global_server.get_plugin_list():  # If the required version of plugin is already exists
            if version_requirement.accept(global_server.get_plugin_metadata(plugin_id).version):
                if is_dependence:
                    logger.info(trans('aluminum.install.dep_installed', plugin_id))
                    return
                elif is_update:
                    logger.info(trans('aluminum.update.already', plugin_id))
                    return
                else:
                    raise PluginAlreadyExistsError(''.join([plugin_id, str(version_requirement)])) from None
            else:
                backup_old_plugin(plugin_id)  # If exists a old version, unload it and make a backup

        if is_dependence:
            logger.info(trans('aluminum.install.install_dep', plugin_id))
        elif is_update:
            logger.info(trans('aluminum.update.updating', plugin_id))
        else:
            logger.info(trans('aluminum.install.installing', plugin_id))

        dependencies = cache['plugins'][plugin_id]['dependencies']
        requirements = cache['plugins'][plugin_id]['requirements']
        if requirements:
            for requirement in requirements:
                pip_install(requirement)
        if dependencies:
            for dependence in dependencies:
                if dependence == 'mcdreforged':
                    continue # TODO
                install_plugin(dependence, dependencies[dependence], is_dependence=True)

        target_asset = get_target_asset()

        download_url = target_asset['browser_download_url']
        if config.use_release_cdn:
            download_url = download_url.replace('https://github.com/', RELEASE_CDN)

        download_file(download_url, target_asset['name'])

        global_server.load_plugin(os.path.join(PLUGIN_FOLDER, target_asset['name']))

    
    except AluminumException as e:
        if is_dependence:
            raise DependenciesInstallError(plugin_id, e)
        else:
            raise


def backup_old_plugin(plugin_id: str):
    if not os.path.isdir(backup_dir):
        os.mkdir(backup_dir)
    if plugin_id in global_server.get_plugin_list():
        plugin_path = global_server.get_plugin_file_path(plugin_id)
        filename = os.path.split(plugin_path)[-1]
        logger.info(trans('aluminum.install.backup', plugin_path))
        global_server.unload_plugin(plugin_id)
        shutil.move(plugin_path, os.path.join(backup_dir, filename + '.bak'))


def refresh_cache():
    global cache
    try:
        # clear_line()
        logger.info(trans('aluminum.cache.refresh'))
        cache = requests.get(plugins_url).json()
        cache['last_refresh'] = time.time()
    except requests.RequestException as e:
        cache['last_refresh'] = 0
        logger.error(trans('aluminum.cache.failed'))
        raise NetworkError(plugins_url, e)
    else:
        logger.info(trans('aluminum.cache.success'))


def check_updates(refresh: bool = False):
    global need_update
    all_meta = global_server.get_all_metadata()
    need_update = {}
    reply_text = []
    if refresh:
        refresh_cache()
    for plg in all_meta:
        try:
            current = all_meta[plg].version
            latest = Version(cache['plugins'][plg]['version'])
            if latest > current:
                need_update[plg] = VersionRequirement(str(latest))
                reply_text.append(f'{plg} ({current} -> {latest})')
        except KeyError:
            continue
    # clear_line()
    if need_update:
        logger.info(trans('aluminum.update.need'))
        for i in reply_text:
            logger.info('§b' + i)
    else:
        logger.info(trans('aluminum.update.none'))


def update_all():
    for i in need_update:
        install_plugin(i, need_update[i], is_update=True)


def get_available_plugins():
    return cache['plugins'].keys() - global_server.get_plugin_list()


def register_command(server: PluginServerInterface):
    def get_literal(literal: str):
        return Literal(literal).requires(lambda src, ctx: src.is_console)

    server.register_command(
        get_literal(config.command_prefix).
        then(get_literal('install').then(
            Text('plugin').suggests(lambda: get_available_plugins()).runs(lambda src, ctx: install_from_string(ctx['plugin']))
        )).
        then(get_literal('update').runs(lambda src: check_updates(refresh=True))
        ).
        then(get_literal('upgrade').runs(lambda src: update_all()).then(
            Text('plugin').suggests(lambda: need_update).
                requires(lambda src, ctx: ctx['plugin'] in need_update).
                runs(lambda src, ctx: install_plugin(ctx['plugin'], need_update[ctx['plugin']], is_update=True))
        )).
        then(get_literal('browse').runs(lambda src: webbrowser.open(PLUGIN_CATALOGUE)
        ))
    )


@new_thread(PLUGIN_ID)
def display_banner():
    time.sleep(1)
    logger.info(BANNER)


def on_load(server: PluginServerInterface, prev_module):
    global cache, need_update, clock
    if hasattr(prev_module, 'cache'):
        cache = prev_module.cache
        need_update = prev_module.need_update
    clock = AluminumClock(config.check_update, check_updates)
    register_command(server)
    with_new_thread(refresh_cache)
    display_banner()
