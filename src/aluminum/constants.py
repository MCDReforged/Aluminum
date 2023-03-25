import sys

import ruamel.yaml as yaml
from mcdreforged.api.all import Serializable, ServerInterface


class Configuration(Serializable):
    permission: int = 3
    source: str = 'https://github.com/'
    update_interval: int = 30
    check_upgrade: bool = True
    plugin_folder: str = 'plugins'
    page_size: int = 6


class NegativeInfinity:
    def __lt__(self, _): return True
    def __le__(self, _): return True
    def __eq__(self, other): return isinstance(other, self)
    def __float__(self, _): return float('-inf')
    def __str__(_): return '-inf'

    def __gt__(self, _): return False
    def __ge__(self, _): return False
    def __ne__(self, other): return not isinstance(other, self)
    def __pos__(self): return self


N_INF = NegativeInfinity()

psi = ServerInterface.get_instance().as_plugin_server_interface()

PYTHON = sys.executable

META = psi.get_self_metadata()
PREFIX = ['!!al', '!!aluminum']

INDEXES = ['api', 'information', 'tool', 'management', 'outdated', 'installed', 'all']
SORTS = ['labels', 'authors', 'name']

DEPENDENCY_BLACKLIST = ['python', 'mcdreforged']

RELOADED_BANNER = f'§3Aluminum {META.version} initialized!'
LOADED_BANNER = f'''                            
§3 _____ _           _               
§3|  _  | |_ _ _____|_|___ _ _ _____ 
§3|     | | | |     | |   | | |     |
§3|__|__|_|___|_|_|_|_|_|_|___|_|_|_|

{RELOADED_BANNER}
'''

