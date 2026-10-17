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
| `quick-access-terminal.conf` | 下拉窗口的位置、高度、输入法兼容的置顶层级 |
| `hotkey/main.c` | Option+空格全局热键源码，调用 Kitty 原生单实例切换 |
| `scripts/install-hotkey.sh` | 检查环境、编译本机程序、生成并加载登录自启动项 |
| `scripts/uninstall-hotkey.sh` | 移除热键程序和自启动项，保留 Kitty 配置 |

## 本机生成的文件

- `~/.local/libexec/kitty-hotkey/kitty-hotkey`：当前机器编译的程序。
- `~/.local/libexec/kitty-hotkey/error.log`：错误日志。
- `~/Library/LaunchAgents/local.kitty.option-space.plist`：当前用户名、Kitty 路径和配置目录对应的自启动设置。

以上文件不需要放进 Git；在新机器运行安装脚本即可重新生成。源码只在仓库内维护。助手仅监听一个快捷键，不记录输入，空闲时阻塞等待系统事件。

## 日常更新与屏幕适配

创建分屏：先按 `Cmd+D`，再按 `← / → / ↑ / ↓`，分别在当前分屏的左、右、上、下创建新分屏；第二步可以继续按住 Cmd。新分屏继承当前目录并获得焦点。原来的单独 `Cmd+D` 和 `Cmd+Ctrl+D` 创建分屏方式已替换。`Cmd+Option+方向键` 仍用于切换已有分屏，`Cmd+Shift+Enter` 用于专注当前分屏／恢复布局。

拉取配置更新后，Kitty 可通过 `Ctrl+Cmd+,` 重载；下拉面板再次调用原生切换命令时会读取其配置。修改热键源码、移动仓库或改变 Kitty 安装位置后，重新运行安装脚本即可；重复安装会替换旧助手，不创建多个自启动任务，也不关闭正在运行的终端会话。

当前面板高度针对 1512×982 屏幕设置：`lines 738px` 加上实测留白约为 786px，**不是自动按屏幕百分比计算**。换屏幕后可在 `quick-access-terminal.conf` 调整 `lines`。如果调整了字体、留白，也应检查实际窗口尺寸。

下拉面板的 `background_opacity` 会覆盖主题值；需要统一透明度时同步修改两个文件。`kitty.conf` 中与主题重复的值以最后加载的 `obsidian.conf` 为准。

## 检查和卸载

```sh
launchctl print "gui/$(id -u)/local.kitty.option-space"
bash scripts/uninstall-hotkey.sh
```

如果安装提示热键注册失败，检查其他应用是否占用 Option+空格，并查看上述错误日志。卸载不会恢复其他应用此前关闭的快捷键。
