import ruamel.yaml as yaml

from aluminum.constants import psi

with psi.open_bundled_file('trans\zh_cn.yml') as f:
    TRANSLATION = yaml.safe_load(f)


def trans(msg, *args):
    if psi.get_mcdr_language() == 'zh_cn':
        try:
            msg = TRANSLATION[msg]
        except:
            msg = f'[未译: {msg}]'
    if args:
        msg = msg.format(*args)
    return msg
