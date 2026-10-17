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

## 文件用途

| 文件 | 用途 |
| --- | --- |
| `kitty.conf` | Kitty 主入口，最后加载主题配置 |
| `obsidian.conf` | 字体、配色、半透明背景、光标动画、分屏快捷键 |
| `vampire-gothic.conf` | 夜魅紫配色覆盖层，统一窗口、标签栏与提示符色调 |
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

创建分屏：先按 `Cmd+D`，再按 `← / → / ↑ / ↓`，分别在当前分屏的左、右、上、下创建新分屏；第二步可以继续按住 Cmd。新分屏继承当前目录并获得焦点。原来的单独 `Cmd+D` 和 `Cmd+Ctrl+D` 创建分屏方式已替换。`Cmd+Option+方向键` 仍用于切换已有分屏，`Cmd+Shift+Enter` 用于专注当前分屏／恢复布局。

拉取配置更新后，Kitty 可通过 `Ctrl+Cmd+,` 重载；下拉面板再次调用原生切换命令时会读取其配置。修改热键源码、移动仓库或改变 Kitty 安装位置后，重新运行安装脚本即可；重复安装会替换旧助手，不创建多个自启动任务，也不关闭正在运行的终端会话。

当前面板高度针对 1512×982 屏幕设置：`lines 738px` 加上实测留白约为 786px，**不是自动按屏幕百分比计算**。换屏幕后可在 `quick-access-terminal.conf` 调整 `lines`。如果调整了字体、留白，也应检查实际窗口尺寸。

下拉面板的 `background_opacity` 会覆盖主题值；需要统一透明度时同步修改两个文件。`kitty.conf` 先加载 `obsidian.conf`，再加载 `vampire-gothic.conf`；重复的配色以最后加载的紫色主题为准。

## 检查和卸载

```sh
launchctl print "gui/$(id -u)/local.kitty.option-space"
bash scripts/uninstall-hotkey.sh
```

如果安装提示热键注册失败，检查其他应用是否占用 Option+空格，并查看上述错误日志。卸载不会恢复其他应用此前关闭的快捷键。
