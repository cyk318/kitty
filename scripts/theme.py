#!/usr/bin/env python3
"""Kitty 配色选择与状态加载；仅依赖 Python 标准库。"""
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / '.theme-state.json'
DEFAULT = 'temptation-purple'
THEMES = [
    ('creamy-ivory', '月光银 Moonstone', '冷银文字、淡灰层次，清淡耐看'),
    ('sage-green', '烟松青 Pine Mist', '灰绿点缀，像雾里的松针'),
    ('midnight-navy', '深海蓝 Deep Ocean', '墨蓝底块，柔和的海盐蓝'),
    ('oxblood-burgundy', '黑樱桃 Black Cherry', '暗樱红与灰玫瑰，浓郁但克制'),
    ('dusty-lavender', '鸢尾灰 Iris Haze', '灰调鸢尾，柔软轻盈'),
    ('sandstone-taupe', '白茶金 White Tea', '茶褐底块，一点柔金'),
    ('cyber-teal', '月下青 Moonlit Teal', '烟青与冷白，去掉荧光感'),
    ('powder-blue', '雨雾蓝 Rain Blue', '灰蓝与雾白，安静清透'),
    ('terracotta', '烟铜色 Smoked Copper', '深咖底块，低饱和的铜色'),
    ('graphite-monochrome', '铅笔灰 Pencil Graphite', '近乎无彩色，干净利落'),
    ('forest-emerald', '墨玉 Jade Ink', '墨绿底块，柔玉色微光'),
    ('champagne-blush', '玫瑰灰 Rose Ash', '灰玫瑰配暖银，轻柔不甜腻'),
    (DEFAULT, '诱惑紫色 Temptation Purple', '原有丝绒紫、银灰与柔玫瑰'),
]
PROMPT_KEYS = {'obsidian', 'velvet', 'rose', 'purple', 'silver', 'muted', 'ivory'}
CURSOR_KEYS = {'cursor', 'cursor_text_color', 'cursor_trail_color'}
KEYS = PROMPT_KEYS | CURSOR_KEYS


def palette(theme):
    """只接受完整的颜色项，状态文件不能注入配置或任意路径。"""
    if theme not in {item[0] for item in THEMES}:
        raise ValueError('未知主题')
    path = ROOT / 'themes' / (theme + '.conf')
    colors = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, value = line.split(None, 1)
        if key not in KEYS or not re.fullmatch(r'#[0-9a-fA-F]{6}', value.strip()):
            raise ValueError(f'主题颜色无效：{path.name} / {key}')
        colors[key] = value.strip().lower()
    if colors.keys() != KEYS:
        raise ValueError(f'主题颜色不完整：{path.name}')
    return colors


def selected():
    try:
        theme = json.loads(STATE.read_text(encoding='utf-8'))['theme']
        palette(theme)
        return theme
    except (OSError, ValueError, KeyError, TypeError):
        return DEFAULT


def emit():
    """原紫色已由静态 include 加载；加载失败时不输出覆盖项。"""
    try:
        colors = palette(selected())
    except (OSError, ValueError, TypeError):
        return
    for key in sorted(CURSOR_KEYS):
        print(key, colors[key])


def prompt_text(theme):
    """只替换 Starship 的调色板，保留布局、符号、模块和 Git 信息。"""
    text = (ROOT / 'starship.toml').read_text(encoding='utf-8')
    colors = palette(theme)
    replacement = '[palettes.vampire]\n' + ''.join(
        f"{key} = '{colors[key]}'\n" for key in sorted(PROMPT_KEYS)) + '\n'
    text, count = re.subn(r'(?ms)^\[palettes\.vampire\]\n.*?(?=^\[|\Z)', replacement, text)
    if count != 1:
        raise ValueError('Starship 基础配置缺少唯一的 vampire 调色板')
    return text.encode('utf-8')


def prompt_config():
    """Shell 初始化时校验状态并修复缓存；内容未变时不写盘。"""
    with (ROOT / '.theme-state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return save_prompt(selected())


def save_prompt(theme):
    path = ROOT / '.theme-state-starship.toml'
    content = prompt_text(theme)
    if not path.exists() or path.read_bytes() != content:
        atomic_write(path, content)
    return path


def atomic_state(content):
    """同目录原子替换，避免退出或断电留下半份 JSON。"""
    atomic_write(STATE, content)


def atomic_write(path, content):
    if content is None:
        path.unlink(missing_ok=True)
        return
    fd, name = tempfile.mkstemp(prefix='.theme-state-', dir=ROOT)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def kitten():
    executable = shutil.which('kitten')
    if not executable:
        executable = '/Applications/kitty.app/Contents/MacOS/kitten'
    if not Path(executable).is_file():
        raise ValueError('找不到 kitten，请先安装 Kitty 并将 kitten 加入 PATH')
    return executable


def remote(address, *args):
    result = subprocess.run([kitten(), '@', '--to', address, *args],
                            capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Kitty 远程命令失败')
    return result.stdout


def targets():
    """复用当前会话 socket，并同步同一配置目录的存活实例。"""
    addresses = []
    current = os.environ.get('KITTY_LISTEN_ON')
    if current:
        remote(current, 'get-colors', '--configured')
        addresses.append(current)
    for path in sorted(ROOT.glob('scrollback-socket-*')):
        if not path.is_socket():
            continue
        address = 'unix:' + str(path)
        if address in addresses:
            continue
        try:
            remote(address, 'get-colors', '--configured')
        except (OSError, ValueError, subprocess.TimeoutExpired):
            continue  # 已退出实例可能留下 socket；不影响当前会话。
        addresses.append(address)
    if not addresses:
        raise ValueError('没有可连接的 Kitty 会话；请在 Kitty 中运行，确认 socket-only 配置已加载')
    return addresses


def switch(theme):
    colors = palette(theme)
    prompt_text(theme)
    # 串行化不同窗口中的菜单；锁文件存在不代表锁仍被占用。
    with (ROOT / '.theme-state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        addresses = targets()
        old = STATE.read_bytes() if STATE.exists() else None
        atomic_state((json.dumps({'theme': theme}) + '\n').encode('utf-8'))
        try:
            save_prompt(theme)
            for address in addresses:
                remote(address, 'load-config')
                actual = dict(line.split(None, 1) for line in
                              remote(address, 'get-colors', '--configured').splitlines() if line.strip())
                if any(actual.get(key) != colors[key] for key in CURSOR_KEYS):
                    raise ValueError('重载后的颜色不匹配，请检查配置覆盖项或 geninclude 是否启用')
        except (OSError, ValueError, subprocess.TimeoutExpired, KeyboardInterrupt):
            atomic_state(old)
            save_prompt(selected())
            for address in addresses:
                try:
                    remote(address, 'load-config')
                except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                    print(f'回退重载失败：{address}：{error}', file=sys.stderr)
            raise
    print(f'已切换：{dict((slug, title) for slug, title, _ in THEMES)[theme]} · 已保存 · 同步 {len(addresses)} 个 Kitty 实例')


def main():
    if sys.argv[1:] == ['--prompt-config']:
        print(prompt_config())
        return
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if len(sys.argv) != 2 or choice not in {item[0] for item in THEMES}:
            raise ValueError('用法：color（交互菜单），或 color <主题英文标识>')
    else:
        active = selected()
        print('\n  提示符与光标 · 色彩书房\n  ' + '─' * 36)
        for number, (slug, title, description) in enumerate(THEMES, 1):
            marker = '●' if slug == active else ' '
            print(f' {marker} {number:2d}  {title} · {description}')
            if sys.stdout.isatty():
                try:
                    print('        ' + preview(slug))
                except (OSError, ValueError):
                    print('        主题文件不可用')
        print('\n  q  退出，不修改当前主题\n')
        while True:
            try:
                answer = input('  选择主题 [1–13 / q]：').strip()
            except EOFError:
                return
            if answer.lower() == 'q':
                return
            if len(answer) <= 2 and answer.isascii() and answer.isdigit() and 1 <= int(answer) <= len(THEMES):
                choice = THEMES[int(answer) - 1][0]
                break
            print('  请输入 1–13，或 q 退出。')
    switch(choice)


def preview(theme):
    """直接用真彩色展示同一布局，选择前就能比较目录块与光标。"""
    colors = palette(theme)

    def paint(text, foreground, background='obsidian'):
        def rgb(key):
            value = colors[key].lstrip('#')
            return ';'.join(str(int(value[i:i + 2], 16)) for i in (0, 2, 4))
        return f'\033[38;2;{rgb(foreground)};48;2;{rgb(background)}m{text}\033[0m'

    return (paint('╭─', 'muted') + paint('', 'velvet') +
            paint(' 󰉋 ~/project ', 'ivory', 'velvet') + paint(' ', 'velvet') +
            paint(' main ', 'silver') + paint('· ', 'muted') +
            paint(' 1 ', 'purple') + paint('❯ ', 'silver') + paint('▌', 'cursor'))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n已取消。', file=sys.stderr)
        sys.exit(130)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f'未完成切换：{error}', file=sys.stderr)
        sys.exit(1)
