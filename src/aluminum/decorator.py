import inspect
import time
from copy import copy
from typing import Callable, Dict, List, Optional, Union

from mcdreforged.api.command import *
from mcdreforged.api.rtext import RAction, RText, RTextList
from mcdreforged.api.types import PluginServerInterface
from mcdreforged.utils.types import MessageText, TranslationKeyDictRich

from aluminum.utils import print_msg, trans


class CommandBuilder:
    type_map = {
        int: Integer,
        float: Number,
        str: QuotableText,
        bool: Boolean,
        enumerate: Enumeration
    }

    def __init__(self, server: PluginServerInterface, literal: Union[List[str], str], help_msg: Optional[Union[MessageText, TranslationKeyDictRich]] = None, type_map: Optional[dict] = None, default_node: Optional[ArgumentNode] = Text) -> None:
        """A MCDR command builder using decorator, based on SimpleCommandBuilder.

        Args:
            server (PluginServerInterface): MCDR PSI. You may wanna use `ServerInterface.get_instance().as_plugin_server_interface()` to get one.
            literal (str): Main literal for the command tree.
            help_msg (MessageText | TranslationKeyDictRich, optional): Help message of the command tree.
            type_map (dict, optional): A map to match type hint with MCDReforged argument nodes.
            default_node (ArgumentNode, optional): Default node when there's no type hint. Defaults to Text.

        Default type map:
            int: Integer
            float: Number
            str: QuotableText
            bool: Boolean
            enumerate: Enumeration
        """

        if isinstance(literal, str):
            self.literal = [literal.strip()]
        else:
            self.literal = [i.strip() for i in literal]
        self._help_msg = help_msg
        self._default_node = default_node
        self._builder = SimpleCommandBuilder()
        self._server = server
        if type_map:
            self.type_map = copy(self.type_map)
            self.type_map.update(type_map)

    def command(self, nodes: Optional[Dict[str, ArgumentNode]] = {}, literal: Optional[Union[List[str], str]] = None):
        """
        Register a subcommand of the main command literal.

        The `literal` parameter specify the name of the sub-literals for the command, respectively. If omitted, the name of the decorated function will be used as the default subliteral.

        The decorated function should take one or more positional parameters, which will be mapped to the corresponding arguments. The parameters can be annotated with their expected types (e.g., `param: str`), which will be used to perform specific node.

        Optional parameters (i.e., those with default values) will be registered as optional arguments.

        Example::

            >>> builder = CommandBuilder("!!manager")
            >>> @builder.command("manage install", "m i")
            ... def install(src, param1: int, param2=None):
            ...     ...

            The command tree would be:
                Literal('!!manager')
                ├─ Literal('manage')
                │   └─ Literal('install')
                │       └─ Integer('param1') -> install(src, ctx['param1'])
                │           └─ Integer('param2') -> install(src, ctx['param1'], ctx['param2'])
                └─ Literal('m')
                    └─ Literal('i')
                        └─ Integer('param1') -> install(src, ctx['param1'])
                            └─ Integer('param2') -> install(src, ctx['param1'], ctx['param2'])
        """

        def decorate(func: Callable, literal=literal):
            if issubclass(type(literal), str):
                literal = [literal]
            if not literal:
                literal = [func.__name__]

            def register_subcommand():
                # e.g. def test(src, a, b: str, c=None)
                def _register(params):
                    params_text = [i.name for i in params]
                    all_params = ' '.join([f'<{p}>' for p in params_text])
                    for main in self.literal:
                        for sub in literal:
                            self._builder.command(f'{main} {sub.strip()} {all_params}',
                                                  lambda src, ctx: func(src, *[ctx[p] for p in params_text]))
                sig = inspect.signature(func)
                params = list(sig.parameters.values())[1:]
                params = [i for i in params if i.default == inspect.Parameter.empty]  # a, b
                optional_params = [i for i in params if i.default != inspect.Parameter.empty]  # c
                for i in range(len(optional_params) + 1):
                    _register(params + optional_params[:i])  # (a, b), (a, b, c)

                for param in params + optional_params:  # a, b, c
                    if param.name in nodes:
                        self._builder.arg(param.name, nodes[param.name])
                        continue
                    if param.annotation == inspect._empty:
                        self._builder.arg(param.name, nodes.get(param.name, self._default_node))
                        continue
                    arg_type = self.type_map.get(param.annotation)
                    if arg_type:
                        self._builder.arg(param.name, arg_type)
                        continue
                    raise ValueError(f'Can\'t find type {param.annotation} in type map.')

            register_subcommand()
            return lambda *args, **kwargs: func(*args, **kwargs)
        return decorate

    def register(self) -> None:
        """
        Register the command tree into server interface.
        :raise SimpleCommandBuilder.Error:
        """
        self._builder.register(self._server)
        if self._help_msg:
            self._server.register_help_message(self.literal[0], self._help_msg)


def execute_on_second_time(timeout_seconds, operation, command):
    sources = {}

    def decorator(func):
        def wrapper(s, src, arg, *args, **kwargs):
            nonlocal sources
            src_id = str(src)
            now = time.time()
            for source, item in sources.items():
                if now - item[1] >= timeout_seconds:
                    sources.pop(source)
            last = sources.get(src_id)
            if last:
                sources.pop(src_id)
                if last[0] == str(arg):
                    return func(s, src, arg, *args, **kwargs)
            print_msg(src, trans('▶ You\'re §l{}§r following plugin(s):', operation))
            print_msg(src, f'  §e§l{arg}§r')
            print_msg(src, RTextList(
                RText(trans('§3§lExecute same command again')). \
                    c(RAction.run_command, command.format(arg)). \
                    h(trans('§3Click to execute')),
                RText(trans('§r to confirm.'))
            ))
            sources[src_id] = (str(arg), time.time())
            return None
        return wrapper
    return decorator
