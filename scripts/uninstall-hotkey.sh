#!/bin/bash
# 只卸载本仓库的热键助手，不退出 Kitty、不修改终端配置或其他软件快捷键。
set -euo pipefail
label=local.kitty.option-space
domain="gui/$(id -u)"
if launchctl print "$domain/$label" >/dev/null 2>&1; then
    launchctl bootout "$domain/$label"
fi
rm -f "$HOME/Library/LaunchAgents/$label.plist" \
    "$HOME/.local/libexec/kitty-hotkey/kitty-hotkey"
echo '全局热键与登录自启动已卸载；Kitty 配置及诊断日志保留。'
