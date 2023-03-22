import os
from threading import Lock
from urllib.parse import urljoin

from mcdreforged.api.all import *

import aluminum.constant as constants
import aluminum.utils as utils
from aluminum.classes import PluginCatalogue, PluginManager

manager: PluginManager
catalogue: PluginCatalogue
config: constants.Configuration
session_lock: Lock = Lock()
global_server = constants.global_server


def print_help_message(src: CommandSource):
    prefix = constants.PREFIX[0]
    def get_button(text, action, command):
        command = f'{prefix} {command}'
        suggest = ' '.join([i for i in command.split(' ') if not i.startswith('<')]) + ' '
        return RTextBase.format('[{}] ', RText(utils.trans(text), RColor.dark_aqua).c(action, suggest).h(command))
    if src.is_console:
        src.reply(
f'''§3§lAluminum§r§a {constants.PLUGIN_VERSION} §r{utils.trans('Usage:')}
{utils.trans('§lBrowse catalogue')}
    §3{prefix} browse <index> [page]
    §3{prefix} browse <index> <sort_by> [page]
    §3{prefix} search <keyword>
    <index: {', '.join(constants.INDEXES)}>
    <sort_by: {', '.join(constants.SORTS)}>
    <keyword: QuotableText>
{utils.trans('§lPlugin Management')}
    §3{prefix} <install|disable|reload> <plugin_id>
    §3{prefix} <load|enable> <file_path>'''
)
        return
    msg = RTextList(RText(f"§3§lAluminum§r§a {constants.PLUGIN_VERSION} §r{utils.trans('Usage:')}"), '\n\n')
    msg = msg.append(
        RTextList(utils.trans('§lBrowse catalogue'), '\n    ',
              get_button('API', RAction.run_command, 'browse api'),
              get_button('Tool', RAction.run_command, 'browse tool'),
              get_button('Management', RAction.run_command, 'browse management'),
              get_button('All', RAction.run_command, 'browse all'), '\n    ',
              get_button('Search', RAction.suggest_command, 'search <keyword>'),
              get_button('Outdated', RAction.run_command, 'browse outdated'),
              get_button('Installed', RAction.run_command, 'browse installed'), '\n'
              )
    )
    msg = msg.append(
        RTextList('\n',
              utils.trans('§lPlugin Management'), '\n    ',
              get_button('Install', RAction.suggest_command, 'install <plugin_id>'),
            #   get_button('Upgrade', RAction.suggest_command, 'upgrade'), '\n    ',
              get_button('List', RAction.run_command, 'list'),
              get_button('Enable', RAction.suggest_command, 'enable <file_path>'),
              get_button('Disable', RAction.suggest_command, 'disable <plugin_id>'),
              get_button('Load', RAction.suggest_command, 'load <file_path>'),
              get_button('Reload', RAction.suggest_command, 'reload <plugin_id>'),
              )
    )
    src.reply(msg)


def register_commands():
    def parse_mcdr_commands(src: PlayerCommandSource, ctx):
        node = ' '.join(src.get_info().content.split()[1:])
        global_server.execute_command(f'!!MCDR plg {node}', src)

    def sort_or_page(src, ctx):
        if utils.is_integer(ctx['sorted_by/page']):
            if src.is_console:
                return int(ctx['sorted_by/page']) == 1
            return 0 < int(ctx['sorted_by/page']) < manager.max_page(ctx['index'], config.page_size)
        else:
            return ctx['sorted_by/page'] in constants.SORTS

    def page(src, ctx):
        validate_sort = ctx['sorted_by/page'] in constants.SORTS if 'sorted_by/page' in ctx else True
        return validate_sort and 0 < ctx['page'] <= (1 if src.is_console else manager.max_page(ctx.get('index', 'all'), config.page_size, ctx.get('keyword', None)))

    def run_browse(src, ctx: dict):
        page_size = None if src.is_console else config.page_size
        if utils.is_integer(ctx.get('sorted_by/page', None)):
            page = int(ctx.get('sorted_by/page', 1))
            return manager.browse(src, ctx.get('index', 'all'), page=page, page_size=page_size, keyword=ctx.get('keyword', None))
        else:
            page = int(ctx.get('page', 1))
            return manager.browse(src, ctx.get('index', 'all'), ctx.get('sorted_by/page', 'name'), page=page, page_size=page_size, keyword=ctx.get('keyword', None))

    global_server.register_command(
        Literal(constants.PREFIX).
        requires(
            lambda src: src.has_permission(config.permission)
        ).runs(print_help_message)
        .then(Literal('test').runs(lambda: print(''))) #!
        .then(
            Literal('update').runs(manager.check_update)
        ).then(
            Literal('install').then(
                QuotableText('plugin_id')
                .suggests(lambda: catalogue.plugins.keys())
                .runs(lambda src, ctx: manager.install(src, ctx['plugin_id'])))
        ).then(
            Literal('disable').then(
                QuotableText('plugin_id')
                .suggests(lambda: manager.plugins.keys())
                .requires(lambda src, ctx: ctx['plugin_id'] in list(manager.plugins.keys()))
                .runs(lambda src, ctx: manager.disable(src, ctx['plugin_id'])))
        ).then(
            Literal('info').then(
                QuotableText('plugin_id')
                .suggests(lambda: list(manager.plugins.keys()) + list(manager.catalogue.plugins.keys()))
                .requires(lambda src, ctx: ctx['plugin_id'] in list(manager.plugins.keys()) + list(manager.catalogue.plugins.keys()))
                .runs(lambda src, ctx: manager.info(src, ctx['plugin_id'])))
        ).then(
            Literal('search').then(
                QuotableText('keyword')
                .runs(run_browse)
                .then(
                    Integer('page')
                    .requires(page)
                    .runs(run_browse)
                ))  # !
        ).then(
            Literal('browse')
            .runs(run_browse)
            .then(
                Text('index')
                .requires(lambda src, ctx: ctx['index'] in constants.INDEXES)
                .suggests(lambda: constants.INDEXES)
                .runs(run_browse)
                .then(
                    Text('sorted_by/page').suggests(lambda: constants.SORTS)
                    .requires(sort_or_page)
                    .runs(run_browse)
                    .then(
                        Integer('page')
                        .requires(page)
                        .runs(run_browse)
                    )
                )
            )  # !
        ).then(
            Literal('enable').then(
                QuotableText('file_path')
                .suggests(lambda: map(os.path.basename, global_server.get_disabled_plugin_list()))
                .runs(parse_mcdr_commands))
        ).then(
            Literal('load').then(
                QuotableText('file_path')
                .suggests(lambda: map(os.path.basename, global_server.get_unloaded_plugin_list()))
                .runs(parse_mcdr_commands))
        ).then(
            Literal(['reload', 'unload']).then(
                QuotableText('plugin_id')
                .suggests(lambda: [i.id for i in manager.plugins])
                .runs(parse_mcdr_commands))
        ).then(
            Literal(['list', 'reloadall', 'ra']).runs(parse_mcdr_commands)
        )
    )
    global_server.register_help_message(constants.PREFIX[0], utils.trans(constants.PLUGIN_DESCRIPTION))


def on_load(server, prev):
    global config, manager, catalogue, session_lock
    # if hasattr(prev, 'session_lock') and type(prev.session_lock) == type(session_lock):
    #     session_lock = prev.session_lock
    utils.print_msg(global_server.get_plugin_command_source(),
                    constants.LOADED_BANNER if not prev else constants.RELOADED_BANNER)
    config = global_server.load_config_simple(target_class=constants.Configuration)
    config.source = urljoin(config.source, constants.PLUGIN_CATALOGUE)
    manager = PluginManager(config, session_lock)
    catalogue = manager.catalogue
    register_commands()


def on_unload(_):
    try:
        manager.scheduler.stop()
    except:
        raise
