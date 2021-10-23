import os
from typing import List
from urllib.parse import urljoin

from mcdreforged.api.all import Serializable, ServerInterface


class Configure(Serializable):
    command_prefix: List[str] = ['al', 'aluminum']
    cache_timeout: int = 1800
    check_update: int = 1800
    use_meta_cdn: bool = True
    use_release_cdn: bool = True


global_server = ServerInterface.get_instance().as_plugin_server_interface()
config = global_server.load_config_simple(target_class=Configure)

PLUGIN_ID = 'aluminum'
PLUGIN_FOLDER = global_server.get_mcdr_config()['plugin_directories'][0]
PLUGIN_INDEX_PATH = 'plugins.json'
PLUGIN_RELEASE_PATH = '{0}/release.json'
META_CDN = 'https://cdn.jsdelivr.net/gh/MCDReforged/PluginCatalogue@meta/' if config.use_meta_cdn else 'https://raw.githubusercontent.com/MCDReforged/PluginCatalogue/meta/'
RELEASE_CDN = 'https://download.fastgit.org/'
PLUGIN_CATALOGUE = 'https://github.com/MCDReforged/PluginCatalogue/tree/catalogue'

logger = global_server.logger
trans = global_server.tr
plugins_url = urljoin(META_CDN, 'plugins.json')
backup_dir = os.path.join(global_server.get_data_folder(), 'backup')

# A regex to get plugin name and version requirement
SEMVER_PATTERN = '(\w+)([><=~^]?=?[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z\d][-a-zA-Z.\d]*)?(\+[a-zA-Z\d][-a-zA-Z.\d]*)?)?'

BANNER = f'''                            
§e _____ _           _               
§e|  _  | |_ _ _____|_|___ _ _ _____ 
§e|     | | | |     | |   | | |     |
§e|__|__|_|___|_|_|_|_|_|_|___|_|_|_|

§eAluminum 0.1.0
                                   
§e感谢使用 Aluminum 作为你的插件管理器.
§cAluminum 是一个用于学习相关知识的项目, 且仍处于测试阶段, 可能不稳定.
'''
