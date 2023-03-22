<p align="center">
    <img src="Al.png" alt="Aluminum Logo" width="200">
</p>

<h1 align="center">Aluminum</h1>

<p align="center">
    Another MCDR Plugin Manager
</p>

<p align="center">
    <a href="https://github.com/MCDReforged/Aluminum/releases"><strong>Try it now »</strong></a>
</p>

## :warning: WARNING
- Aluminum is a project for learning purposes, makes no, and and hereby disclaims any warranties express or implied.
- Aluminum is still in alpha test. Highly unstable and unreadable code included. Not ready for production environment.

## Commands
| Command | Short form | Function |
| - | - | - |
| !!al update | - | Update catalogue cache |
| !!al upgrade | - | Upgrade all outdated plugins |
| !!al browse \<index\> [page] | !!al b \<index\> [page] | Browse catalogue |
| !!al browse \<index\> \<sort_by\> [page] | !!al b \<index\> \<sort_by\> [page] | Browse catalogue |
| !!al search \<keyword\> | !!al s \<keyword\> | Search catalogue |
| !!al info \<keyword\> | - | Show plugin infomation |
| !!al install \<plugin_id\> | !!al i \<plugin_id\> | Install a plugin |
| !!al disable \<plugin_id\> | !!al d \<plugin_id\> | Disable a plugin |
| !!al reload \<plugin_id\> | !!al r \<plugin_id\> | Reload a plugin |
| !!al load \<file_path\> | !!al l \<file_path\> | Load a plugin from file |
| !!al enable \<file_path\> | !!al e \<file_path\> | Enable a plugin |

| Parameter | Definition |
| - | - |
| index | One of `api`, `information`, `tool`, `management`, `outdated`, `installed`, `all` |
| sort_by | `labels`, `authors`, `name` |
| page | Optional, a `Integer` |
| keyword | A `QuotableText` |
| plugin_id | A `Text` |
| file_path | A `QuotableText` |

## Configuration
```json5
{
    "permission": 3,
    // Permission required to use commands.

    "source": "https://github.com/",
    // Catalogue source. You may use ghproxy/fastgit to get faster speed:
    // "source": "https://ghproxy.com/https://github.com/"
    // "source": "https://hub.fgit.ml/"

    "update_interval": 1000,
    // Catalogue update interval in seconds.

    "check_upgrade": true,
    // Whether to check plugin upgrades on catalogue update.

    "plugin_folder": "plugins",
    // Plugin folder for installation. Should be a MCDR plugin folder.

    "page_size": 6,
    // Page size when browsing and searching catalogue.
}
```

## TODO
### March ~ April, 2023
- [ ] Take class `Session` out
- [ ] Implement `!!al upgrade`
- [x] Better README

### May, 2023
- [ ] Handle all exceptions
- [ ] Better i18n
- [ ] Consider to use 3rd party API
- [ ] Clear the codes

## Special Thanks
- [`MPM`](https://github.com/Ivan-1F/MCDReforgedPluginManager) by Ivan-1F
- [`ChatGPT`](https://openai.com/blog/chatgpt) by OpenAI (what)
