
from mcdreforged.utils.serializer import Serializable


class ValueDict(dict):
    def __iter__(self):
        return iter(self.values())


class PrettySerializable(Serializable):
    def represent(self) -> str:
        """
        aka repr
        """
        return '{}[{}]'.format(type(self).__name__, ','.join([
            '{}={}'.format(k, repr(v)) for k, v in vars(self).items() if not k.startswith('_')
        ]))

    def __repr__(self) -> str:
        return self.represent()
