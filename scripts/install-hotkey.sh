#!/bin/bash
# 在当前 Mac 编译全局热键助手，并注册用户登录自启动；可重复执行。
set -euo pipefail

case "${1:-}" in
    ""|--check) ;;
    *) echo "用法：$0 [--check]" >&2; exit 2 ;;
esac
[[ "$(uname -s)" == Darwin ]] || { echo '仅支持 macOS。' >&2; exit 1; }
repo_dir="$(cd "$(dirname "$0")/.." && pwd -P)"
label=local.kitty.option-space
domain="gui/$(id -u)"
runtime_dir="$HOME/.local/libexec/kitty-hotkey"
agent_path="$HOME/Library/LaunchAgents/$label.plist"

# 优先采用显式指定的位置，兼容系统 Applications 和用户 Applications。
kitty_app="${KITTY_APP:-}"
if [[ -z "$kitty_app" ]]; then
    for candidate in /Applications/kitty.app "$HOME/Applications/kitty.app"; do
        if [[ -x "$candidate/Contents/MacOS/kitten" ]]; then
            kitty_app="$candidate"
            break
        fi
    done
fi
[[ -n "$kitty_app" && -x "$kitty_app/Contents/MacOS/kitty" && -x "$kitty_app/Contents/MacOS/kitten" ]] || {
    echo '未找到 Kitty；请先安装，或通过 KITTY_APP=/绝对路径/kitty.app 指定。' >&2
    exit 1
}
kitty_app="$(cd "$kitty_app" && pwd -P)"
xcrun --find clang >/dev/null 2>&1 || {
    echo '需要 Apple Command Line Tools；请先运行 xcode-select --install。' >&2
    exit 1
}
launchctl print "$domain" >/dev/null 2>&1 || {
    echo '请在当前用户已登录的 macOS 图形会话中执行。' >&2
    exit 1
}

# 使用当前 Kitty 自己的解析器检查配置与所需原生功能，不安装或升级软件。
KITTY_CONFIG_DIRECTORY="$repo_dir" "$kitty_app/Contents/MacOS/kitty" +runpy '
import os
from kitty.config import load_config
from kitty.options.types import defaults
assert hasattr(defaults, "custom_shaders") and hasattr(defaults, "macos_ns_window_layer"), "请使用支持当前配置的 Kitty 0.49.2 或更新版本"
errors = []
load_config(os.path.join(os.environ["KITTY_CONFIG_DIRECTORY"], "kitty.conf"), accumulate_bad_lines=errors)
assert not errors, errors
'
if [[ "${1:-}" == --check ]]; then
    printf '预检通过。\nKitty：%s\n配置目录：%s\n' "$kitty_app" "$repo_dir"
    exit 0
fi

# 先准备编译产物与本机 plist，成功后才替换现有助手，避免编译失败中断热键。
build_dir="$(mktemp -d "${TMPDIR:-/tmp}/kitty-hotkey.XXXXXX")"
trap 'rm -rf "$build_dir"' EXIT
xcrun clang -Wall -Wextra -Werror -O2 -x objective-c -framework Carbon -framework Cocoa \
    "$repo_dir/hotkey/main.c" -o "$build_dir/kitty-hotkey"
plist="$build_dir/$label.plist"
/usr/bin/plutil -create xml1 "$plist"
/usr/bin/plutil -insert Label -string "$label" "$plist"
/usr/bin/plutil -insert ProgramArguments -json '[]' "$plist"
/usr/bin/plutil -insert ProgramArguments.0 -string "$runtime_dir/kitty-hotkey" "$plist"
/usr/bin/plutil -insert ProgramArguments.1 -string "$kitty_app/Contents/MacOS/kitten" "$plist"
/usr/bin/plutil -insert EnvironmentVariables -json '{}' "$plist"
/usr/bin/plutil -insert EnvironmentVariables.KITTY_CONFIG_DIRECTORY -string "$repo_dir" "$plist"
/usr/bin/plutil -insert WorkingDirectory -string "$HOME" "$plist"
/usr/bin/plutil -insert RunAtLoad -bool true "$plist"
/usr/bin/plutil -insert KeepAlive -bool true "$plist"
/usr/bin/plutil -insert ThrottleInterval -integer 30 "$plist"
/usr/bin/plutil -insert LimitLoadToSessionType -string Aqua "$plist"
/usr/bin/plutil -insert StandardErrorPath -string "$runtime_dir/error.log" "$plist"
/usr/bin/plutil -lint "$plist"

mkdir -p "$runtime_dir" "$HOME/Library/LaunchAgents"
if launchctl print "$domain/$label" >/dev/null 2>&1; then
    launchctl bootout "$domain/$label"
fi
/usr/bin/install -m 755 "$build_dir/kitty-hotkey" "$runtime_dir/kitty-hotkey.new"
mv -f "$runtime_dir/kitty-hotkey.new" "$runtime_dir/kitty-hotkey"
/usr/bin/install -m 644 "$plist" "$agent_path"
launchctl bootstrap "$domain" "$agent_path"
sleep 1
if ! launchctl print "$domain/$label" | /usr/bin/awk '/state = running/ { ok=1 } END { exit !ok }'; then
    printf '助手未保持运行，请检查热键冲突及日志：%s/error.log\n' "$runtime_dir" >&2
    exit 1
fi
printf '已安装：Option+空格显示/隐藏 Kitty，登录后自动启动。\n源码与配置：%s\n' "$repo_dir"
