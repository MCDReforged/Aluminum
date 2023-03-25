import os

from mcdreforged.api.all import *
from ruamel.yaml import YAML, CommentedMap

from aluminum.constants import psi


class Configuration(Serializable):
    CONFIG_PATH = os.path.join(psi.get_data_folder(), 'config.yml')
    DEFAULT_CONFIG = psi.open_bundled_file('resources/default_config.yml')

    permission: int = 3
    source: str = 'https://github.com/MCDReforged/PluginCatalogue/archive/refs/heads/meta.zip'
    update_interval: int = 30
    check_upgrade: bool = True
    plugin_folder: str = 'plugins'
    page_size: int = 6

    @property
    def request_proxy(self) -> dict:
        param = {}
        for k, v in self.proxy.serialize().items():
            if v is not None:
                param[k] = v
        return param if param else None

    @classmethod
    def load(cls) -> 'Configuration':
        if not os.path.isfile(cls.CONFIG_PATH):
            cls.__save_default()
            default = cls.get_default()
            return default
        with open(cls.CONFIG_PATH, 'r', encoding='utf8') as f:
            data = YAML().load(f)
        return cls.deserialize(data)

    @classmethod
    def __save_default(cls):
        if not os.path.isdir(os.path.dirname(cls.CONFIG_PATH)):
            os.makedirs(os.path.dirname(cls.CONFIG_PATH))
        with open(cls.CONFIG_PATH, 'w', encoding='utf8') as file:
            data: CommentedMap = YAML().load(cls.DEFAULT_CONFIG)
            YAML().dump(data, file)


config = Configuration.load()
