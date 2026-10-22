# source 一次或多次均可；路径在加载时确定，调用不依赖当前目录。
typeset -g KITTY_THEME_SCRIPT="${${(%):-%x}:A:h}/theme.py"
function color() {
    python3 "$KITTY_THEME_SCRIPT" "$@"
}

# 所有已加载入口的 Shell 共用同一份生成配置，Starship 每次绘制时读取。
# 初始化时校验/修复缓存，不增加 precmd 钩子，避免改变上一条命令的退出码。
function _kitty_theme_prompt() {
    local theme_config
    if theme_config=$(python3 "$KITTY_THEME_SCRIPT" --prompt-config); then
        export STARSHIP_CONFIG="$theme_config"
    else
        export STARSHIP_CONFIG="${KITTY_THEME_SCRIPT:h:h}/starship.toml"
    fi
}
_kitty_theme_prompt
