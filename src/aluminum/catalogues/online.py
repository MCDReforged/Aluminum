import json
import os
from typing import Dict
from aluminum.catalogues.plugin import PluginMeta
from aluminum.constants import psi
from aluminum.utils.file import touch_dir

class PluginCatalogue:
    CACHE_PATH = touch_dir(os.path.join(psi.get_data_folder(), 'PluginCatalogue-meta'))
    plugins: Dict[str, PluginMeta]

    def __init__(self) -> None:
        pass
    
    @classmethod
    def load(cls: 'PluginCatalogue') -> 'PluginCatalogue':
        obj = cls()
        if os.path.isfile(os.path.join(cls.CACHE_PATH, '.last_update')):
            obj.plugins = {}
            for subdir, _, _ in os.walk(cls.CACHE_PATH):
                if subdir != cls.CACHE_PATH:
                    with open(os.path.join(subdir, 'plugin.json'), 'r', encoding='utf8') as f:
                        plugin_json = json.load(f)
                    with open(os.path.join(subdir, 'release.json'), 'r', encoding='utf8') as f:
                        release_json = json.load(f)
                    with open(os.path.join(subdir, 'meta.json'), 'r', encoding='utf8') as f:
                        meta_json = json.load(f)
                    plg = PluginMeta.of(meta_json, plugin_json, release_json)
                    obj.plugins[plg.id] = plg
        return obj