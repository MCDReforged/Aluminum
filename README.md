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
Use `!!al` for help

## Configuration
```python
class CatalogueConfig(Serializable):
    source: str = 'https://github.com/' # You may use ghproxy/fastgit to get faster speed
    update_interval: int = 30
    check_upgrade: bool = True
    plugin_folder: str = 'plugins'


class Configuration(Serializable):
    permission: int = 3
    catalogue: CatalogueConfig = CatalogueConfig()
    page_size: int = 6
    use_release_cdn: bool = True
```

## TODO
### March ~ April, 2023
- [ ] Take class `Session` out
- [ ] Implement `!!al upgrade`
- [ ] Better README

### May, 2023
- [ ] Handle all exceptions
- [ ] Better i18n
- [ ] Consider to use 3rd party API
- [ ] Clear the codes

## Special Thanks
- [`MPM`](https://github.com/Ivan-1F/MCDReforgedPluginManager) by Ivan-1F
- [`ChatGPT`](https://openai.com/blog/chatgpt) by OpenAI (what)
