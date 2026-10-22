# Kitty 配置与 Option+空格全局热键

本仓库包含终端配置和原生热键助手源码。新 Mac 不需要重写热键程序，只需要编译并注册一次。二进制和 LaunchAgent 由安装脚本在本机生成，不提交到 Git，因此不会绑定某个用户名或 CPU 架构。

## 新 Mac 安装

1. 安装 Kitty（本配置在 0.49.2 验证）、JetBrainsMono Nerd Font Mono 字体，以及 Apple Command Line Tools（`xcode-select --install`）。脚本不会自动安装这些软件。
2. 将本仓库克隆到 `~/.config/kitty`。如果该目录已有配置，先自行整理，不直接覆盖。
3. 如果 iTerm2 或其他工具占用了 Option+空格，先在对应工具中关闭该热键。不要同时给 macOS 的“Quick access to kitty”服务绑定相同快捷键。
4. 执行：

```sh
cd ~/.config/kitty
bash scripts/install-hotkey.sh --check
bash scripts/install-hotkey.sh
```

完成后按 **Option+空格** 显示/隐藏下拉终端，重启后登录当前用户会自动注册热键。无需手动运行助手，也无需 sudo。使用 macOS 原生 Carbon 热键 API，不安装第三方键盘工具。

安装脚本自动查找 `/Applications/kitty.app` 和 `~/Applications/kitty.app`；其他路径可指定：

```sh
KITTY_APP="/其他路径/kitty.app" bash scripts/install-hotkey.sh
```

## 提示符与光标色调菜单

在 Zsh 的 `~/.zshrc` 中加入以下一行，已有这行时无需重复添加：

```zsh
[[ -r "$HOME/.config/kitty/scripts/color.zsh" ]] && source "$HOME/.config/kitty/scripts/color.zsh"
```

新开终端后运行 `color`，输入 1–13 选择主题，输入 `q` 或按 Ctrl+C 取消。
已经打开的 Shell 可以先运行 `source ~/.config/kitty/scripts/color.zsh`，无需重启正在运行的任务。
支持 `color sage-green` 这样的直接选择；英文标识见 `themes/*.conf`，原紫色标识为 `temptation-purple`。
依赖 Python 3 与 Kitty 的 `kitten` 命令，本机验证版本为 Kitty 0.49.2。

菜单包含月光银、烟松青、深海蓝、黑樱桃、鸢尾灰、白茶金、月下青、雨雾蓝、烟铜色、铅笔灰、墨玉、玫瑰灰，以及原样保留的默认诱惑紫色。新配色统一采用暗色目录块、柔和文字和低饱和点缀，避免浅色大块与荧光色抢眼。交互菜单会直接显示提示符和光标色样。
主题文件的英文标识和编号沿用旧值，兼容已有保存状态与命令；例如 `color sage-green` 现在选择烟松青，`color sandstone-taupe` 选择白茶金。
每套配色覆盖两行 Starship 提示符的目录胶囊、Git 分支/状态、连接线、图标、箭头和右侧环境信息，以及 Kitty 输入光标和拖尾。终端背景、普通正文、选区、标签栏和 ANSI 调色板保持原紫色配置；字体、透明度、布局、光标形状、动画和快捷键也保持原样。

选择结果原子保存到 `.theme-state.json`，不进入 Git。`starship.toml` 保留原始布局和默认配色，脚本只替换它的调色板，生成 `.theme-state-starship.toml`，再通过 `STARSHIP_CONFIG` 加载。已加载新版 `color.zsh` 的各个 Shell 共用此文件，在下一次显示提示符时使用新配色，不重画历史内容、不向正在运行的程序发送按键。旧 Shell 须先各执行一次 `source ~/.config/kitty/scripts/color.zsh`；新 Shell 自动加载。
`kitty.conf` 通过 `geninclude scripts/theme-load.py` 仅输出三个光标颜色项。状态缺失、损坏、未知主题或主题内容不完整时回退原紫色；Shell 初始化时也会校验状态并修复生成的 Starship 配置，不执行状态文件里的内容。
光标切换复用当前会话的 `KITTY_LISTEN_ON` 和工程目录中存活的 `scrollback-socket-*`，通过原生 `load-config` 同步实例的窗口和 Tab，并回读光标颜色确认结果。沿用 `socket-only` 权限，其他配置目录或未开放 socket 的独立实例不保证即时同步。没有可连接实例时不保存选择；重载失败或颜色不匹配时恢复原状态与提示符配置，并尝试重新加载各实例，回退失败会明确提示。并发切换通过文件锁串行执行。

原生机制参考：[Starship 调色板与配置路径](https://starship.rs/config/)、[Kitty 配置生成与加载](https://sw.kovidgoyal.net/kitty/conf/)、[远程配置重载](https://sw.kovidgoyal.net/kitty/remote-control/)。

验证（2026-10-22）：

- `python3 scripts/test-theme.py`：7 项离线回归，覆盖配色白名单、损坏状态、主题缺失/非法内容、失败回退、持久化、菜单退出/无效输入，以及只替换 Starship 调色板和损坏缓存修复。
- 13 套主题逐一调用真实 `starship prompt`，渲染结果各不相同，保留两行结构；测试环境最初使用 `TERM=dumb` 被 Starship 拒绝，改用 `TERM=xterm-kitty` 后通过。
- 当前实例的 3 个分屏逐项回读光标和拖尾颜色匹配，全部非光标颜色与原紫色基线一致；最后恢复诱惑紫色。
- Zsh 语法检查、重复加载入口、新交互 Shell 的配置路径与 `git diff --check` 通过；未增加 precmd 钩子，不干扰现有 Starship 的命令退出码采集。
- 以上是渲染和颜色值验证，个人审美仍以实际观感为准。
- 重新调色后，13 套真实 Starship 渲染、光标回读和非光标配色不变检查通过。12 套新配色中，目录文字/只读提示相对目录块、Git/状态/连接线/光标相对配置背景的最低计算对比度为 5.43:1；此数值不包含桌面透过透明背景后的影响。默认紫色未改动。

## 文件用途

| 文件 | 用途 |
| --- | --- |
| `kitty.conf` | Kitty 主入口，最后加载主题配置 |
| `obsidian.conf` | 字体、配色、半透明背景、光标动画、分屏快捷键 |
| `vampire-gothic.conf` | 夜魅紫配色覆盖层，统一窗口、标签栏与提示符色调 |
| `themes/*.conf` | 13 套提示符调色板与光标颜色 |
| `scripts/color.zsh`、`scripts/theme.py` | `color` 入口、交互菜单、同步与持久化 |
| `scripts/theme-load.py` | Kitty 启动和重载时校验状态并仅输出光标颜色 |
| `starship.toml` | Starship 双行提示符，目录与 Git 在上行，环境与耗时在第二行右侧 |
| `quick-access-terminal.conf` | 下拉窗口的位置、高度、输入法兼容的置顶层级 |
| `shaders/obsidian-focus.pipeline` | 原生分屏焦点光效与非当前分屏轻微暗化的参数 |
| `hotkey/main.c` | Option+空格全局热键源码，调用 Kitty 原生单实例切换 |
| `scripts/install-hotkey.sh` | 检查环境、编译本机程序、生成并加载登录自启动项 |
| `scripts/uninstall-hotkey.sh` | 移除热键程序和自启动项，保留 Kitty 配置 |

## Starship 提示符

提示符配置与 Kitty 一起由 Git 管理，但由 Zsh 加载。新电脑克隆后需安装 Starship 和上述 Nerd Font；例如使用 Homebrew：

```sh
brew install starship
```

在现有 `~/.zshrc` 中合并以下设置，保留自己的插件、别名和快捷键。不要直接覆盖整个文件，也不要重复添加已有的 Starship 初始化。

在加载 Oh My Zsh、Conda 和 virtualenv 之前设置：

```zsh
ZSH_THEME=""
export CONDA_CHANGEPS1=false
export VIRTUAL_ENV_DISABLE_PROMPT=1
```

在 `~/.zshrc` 末尾、环境管理器初始化之后设置：

```zsh
export STARSHIP_CONFIG="$HOME/.config/kitty/starship.toml"
if (( $+commands[starship] )); then
  eval "$(starship init zsh)"
fi
```

执行 `exec zsh` 或新开终端生效。路径使用 `$HOME`，不依赖本机用户名；之后拉取 `starship.toml` 更新会在下次提示符渲染时生效。Conda 环境（包括 `base`）显示在第二行右侧，Python、Node.js 和 JDK 信息按项目出现；Kotlin 只显示项目标识，避免每次渲染启动编译器。

无需把个人 `~/.zshrc`、凭据或本机备份提交到本仓库。本仓库的热键助手面向 macOS，Starship 配置本身可供其他安装了 Zsh、Starship 和 Nerd Font 的电脑使用。

## 本机生成的文件

- `~/.local/libexec/kitty-hotkey/kitty-hotkey`：当前机器编译的程序。
- `~/.local/libexec/kitty-hotkey/error.log`：错误日志。
- `~/Library/LaunchAgents/local.kitty.option-space.plist`：当前用户名、Kitty 路径和配置目录对应的自启动设置。

以上文件不需要放进 Git；在新机器运行安装脚本即可重新生成。源码只在仓库内维护。助手仅监听一个快捷键，不记录输入，空闲时阻塞等待系统事件。

## 日常更新与屏幕适配

视觉效果采用原生光标运动模糊、220 毫秒的分屏焦点光效，以及非当前分屏的轻微暗化。焦点动画结束后停止；静态暗化不主动请求连续动画帧，半透明背景与标签栏配色保留。参数均有中文注释，位于 `shaders/obsidian-focus.pipeline`；无需安装插件或重编译热键助手。

键盘提示标签使用紫底银白色字母标记。按下面的快捷键后输入目标旁边的字母即可选择，按 `Esc` 取消：

| 快捷键 | 操作 |
| --- | --- |
| `Ctrl+E` | 选择屏幕上的链接并用默认浏览器打开 |
| `Ctrl+P` → `F` | 选择屏幕中的文件路径并插入命令行 |
| `Cmd+Shift+P` | 选择文件路径并复制到剪贴板 |
| `Cmd+Shift+Y` | 选择整行内容并复制到剪贴板 |

先按 `Ctrl+P`，松开后再按 `F`，然后输入路径旁的标签字母；路径会插入当前命令行，不自动执行。该前缀也支持 Kitty 原有的其他第二按键：`Shift+F` 打开路径、`C` 选择文件、`D` 选择目录、`L` 插入整行、`W` 插入单词、`H` 插入哈希、`N` 打开文件行号、`Y` 打开超链接。

Hints 标签作用于当前终端屏幕；`C`/`D` 打开文件选择器。`Cmd+Shift+P` 和 `Cmd+Shift+Y` 只复制到剪贴板。原有 `Ctrl+Shift+P` 前缀仍可使用。

`Ctrl+P` 和 `Ctrl+E` 由 Kitty 接管，不再传给 Shell 或终端内程序；Zsh 中可用方向键上键查上一条历史，用 `End` 或 `Ctrl+F` 移动光标。

创建分屏：直接按 `Cmd+← / → / ↑ / ↓`，分别在当前分屏的左、右、上、下创建新分屏。新分屏继承当前目录并获得焦点。`Cmd+Option+方向键` 仍用于切换已有分屏，`Cmd+Shift+Enter` 用于专注当前分屏／恢复布局。

拉取配置更新后，Kitty 可通过 `Ctrl+Cmd+,` 重载；下拉面板再次调用原生切换命令时会读取其配置。修改热键源码、移动仓库或改变 Kitty 安装位置后，重新运行安装脚本即可；重复安装会替换旧助手，不创建多个自启动任务，也不关闭正在运行的终端会话。

Option+空格每次按下时，热键助手根据鼠标所在显示器重新计算尺寸：横向占满屏幕，窗口高度为屏幕高度的 80%，顶部对齐菜单栏下方。通过原生 center 面板及底部外边距控制整个窗口，字体、缩放和内部留白不会额外增加窗口高度。切换显示器后，把鼠标移到目标屏幕再按热键即可。更新后运行 `bash scripts/install-hotkey.sh` 安装助手；无需关闭终端会话。直接运行 `kitten quick-access-terminal` 不经过助手时，仍使用配置中的固定备用高度。

下拉面板的 `background_opacity` 会覆盖主题值；需要统一透明度时同步修改两个文件。`kitty.conf` 先加载 `obsidian.conf`，再加载 `vampire-gothic.conf`；重复的配色以最后加载的紫色主题为准。

## 用 Neovim 查看终端历史

已接入 `kitty-scrollback.nvim`，由 `~/.config/nvim` 的 lazy.nvim 配置加载，固定版本为 v9.3.1。

| 快捷键 | 操作 |
| --- | --- |
| `Ctrl+Shift+H` | 在 Neovim 中查看当前终端保留的历史输出 |
| `Ctrl+Shift+G` | 只查看上一条 Shell 命令的输出 |

进入后用 `/关键词` 搜索、`n` / `N` 跳转、`v` 选择文本，`空格 y` 复制到系统剪贴板并返回终端；`:qa!` 退出。上一条命令输出依赖 Kitty Shell integration 的命令边界标记。

首次配置后保存工作并完全退出、重新打开 Kitty，使 Unix socket 监听生效；只重载配置不足以启用监听。普通窗口和下拉终端共用这些快捷键。在 Kitty 内运行 `nvim +'KittyScrollbackCheckHealth'` 可检查完整链路。

## 检查和卸载

```sh
launchctl print "gui/$(id -u)/local.kitty.option-space"
bash scripts/uninstall-hotkey.sh
```

如果安装提示热键注册失败，检查其他应用是否占用 Option+空格，并查看上述错误日志。卸载不会恢复其他应用此前关闭的快捷键。
