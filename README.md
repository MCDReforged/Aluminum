<img align="left" src="Al.png" alt="MCDR logo" width="200"></img>

# Aluminum

 一个 MCDReforged 插件管理器。
 [![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)、

## :warning: 注意
Aluminum 是一个**纯控制台**插件，一切指令都不能被玩家执行。

## 指令
| 指令 | 参数 | 用途 |
| - | - | - |
| browse | - | 浏览插件库 |
| install | plugin_id | 安装插件 |
| update | - | 手动更新插件库索引 | 
| upgrade | [plugin_id] | 更新一个或所有插件 |

## 配置文件
| 配置项 | 类型 | 默认 | 说明 |
| - | - | - | - |
| command_prefix | `List[str]` | `["al", "aluminum"]` | 命令前缀 |
| cache_timeout | `int` | `1800` | 插件库索引过期时间（秒） |
| check_update | `int` | `1800` | 检查更新间隔（秒） |
| use_meta_cdn | `bool` | `True` | 插件库索引是否使用 CDN |
| use_release_cdn | `bool` | `True` | 下载插件是否使用 CDN |

## FAQ

<details>
  <summary>为什么是纯控制台插件？</summary>
  
  > 大部分 MCDR 插件需要在安装后进行修改配置文件等操作。更新插件后，也需要人工检查插件是否正常。我认为在游戏中执行命令非常浪费时间。当然，如果有人需要，后期会考虑修改。
</details>