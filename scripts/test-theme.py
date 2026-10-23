#!/usr/bin/env python3
"""离线异常回归：所有状态写入临时目录，不连接用户 Kitty。"""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('theme', Path(__file__).with_name('theme.py'))
theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme)


class ThemeTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='kitty theme test ')
        root = Path(self.directory.name)
        shutil.copytree(theme.ROOT / 'themes', root / 'themes')
        shutil.copy(theme.ROOT / 'vampire-gothic.conf', root)
        shutil.copy(theme.ROOT / 'starship.toml', root)
        self.root = patch.object(theme, 'ROOT', root)
        self.state = patch.object(theme, 'STATE', root / '.theme-state.json')
        self.root.start()
        self.state.start()

    def tearDown(self):
        self.state.stop()
        self.root.stop()
        self.directory.cleanup()

    def test_complete_palettes_and_default(self):
        self.assertEqual(theme.selected(), theme.DEFAULT)
        for slug, _, _ in theme.THEMES:
            self.assertEqual(set(theme.palette(slug)), theme.KEYS)
        original = theme.palette(theme.DEFAULT)
        self.assertEqual(original['velvet'], '#38264f')

    def test_invalid_state_falls_back_without_config_injection(self):
        for content in (b'{', b'[]', b'null', b'{"theme":[]}',
                        b'{"theme":"../../outside"}', b'\xff'):
            theme.atomic_state(content)
            self.assertEqual(theme.selected(), theme.DEFAULT)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                theme.emit()
            self.assertIn('cursor #c4addf', output.getvalue())
            self.assertEqual({line.split()[0] for line in output.getvalue().splitlines()},
                             set(theme.terminal_colors(theme.palette(theme.DEFAULT))) | {'action_alias'})

    def test_missing_or_corrupt_theme_falls_back(self):
        theme.atomic_state(b'{"theme":"creamy-ivory"}')
        path = theme.ROOT / 'themes/creamy-ivory.conf'
        path.write_text('background #ffffff\nshell malicious\n', encoding='utf-8')
        self.assertEqual(theme.selected(), theme.DEFAULT)
        path.unlink()
        self.assertEqual(theme.selected(), theme.DEFAULT)
        with self.assertRaises(OSError):
            theme.switch('creamy-ivory')

    def test_failure_restores_exact_state_and_reloads_all_targets(self):
        original = b'{"theme":"temptation-purple"}\n'
        theme.atomic_state(original)
        with patch.object(theme, 'targets', return_value=['one', 'two']), \
             patch.object(theme, 'remote', side_effect=[ValueError('failed'), '', '']) as remote:
            with self.assertRaises(ValueError):
                theme.switch('creamy-ivory')
            self.assertEqual(theme.STATE.read_bytes(), original)
            self.assertEqual(remote.call_count, 3)

    def test_success_persists_and_mismatch_rolls_back(self):
        colors = theme.terminal_colors(theme.palette('creamy-ivory'))
        output = '\n'.join(f'{key} {value}' for key, value in colors.items())
        with patch.object(theme, 'targets', return_value=['one']), \
             patch.object(theme, 'remote', side_effect=['', output]), \
             contextlib.redirect_stdout(io.StringIO()):
            theme.switch('creamy-ivory')
        self.assertEqual(theme.selected(), 'creamy-ivory')

        with patch.object(theme, 'targets', return_value=['one']), \
             patch.object(theme, 'remote', side_effect=['', output, '']):
            with self.assertRaises(ValueError):
                theme.switch('sage-green')
        self.assertEqual(theme.selected(), 'creamy-ivory')

    def test_terminal_mismatch_restores_state_even_when_cursor_matches(self):
        theme.atomic_state(b'{"theme":"sage-green"}')
        colors = theme.terminal_colors(theme.palette('creamy-ivory'))
        colors['background'] = '#ffffff'
        output = '\n'.join(f'{key} {value}' for key, value in colors.items())
        with patch.object(theme, 'targets', return_value=['one']), \
             patch.object(theme, 'remote', side_effect=['', output, '']):
            with self.assertRaises(ValueError):
                theme.switch('creamy-ivory')
        self.assertEqual(theme.selected(), 'sage-green')

    def test_backgrounds_stay_near_black_without_opacity_overrides(self):
        for slug, _, _ in theme.THEMES:
            colors = theme.terminal_colors(theme.palette(slug))
            self.assertLessEqual(max(int(colors['background'][i:i + 2], 16)
                                     for i in (1, 3, 5)), 25)
            self.assertNotIn('background_opacity', colors)

    def test_menu_cancel_eof_invalid_and_selection(self):
        for answers in (['q'], ['bad', '0', str(len(theme.THEMES) + 1), '9' * 5000, 'q'], [EOFError()]):
            with patch('builtins.input', side_effect=answers), \
                 patch.object(theme.sys, 'argv', ['color']), \
                 patch.object(theme, 'switch') as switch, \
                 contextlib.redirect_stdout(io.StringIO()):
                theme.main()
                switch.assert_not_called()
        for number, expected in [('13', theme.DEFAULT), ('14', 'aurora-ink'), ('15', 'plum-apricot')]:
            with patch('builtins.input', return_value=number), \
                 patch.object(theme.sys, 'argv', ['color']), \
                 patch.object(theme, 'switch') as switch, \
                 contextlib.redirect_stdout(io.StringIO()):
                theme.main()
                switch.assert_called_once_with(expected)

    def test_prompt_only_changes_palette_and_repairs_cache(self):
        original = (theme.ROOT / 'starship.toml').read_text(encoding='utf-8')
        pattern = r'(?ms)^\[palettes\.vampire\]\n.*?(?=^\[|\Z)'
        import re
        for slug, _, _ in theme.THEMES:
            actual = theme.prompt_text(slug).decode('utf-8')
            self.assertEqual(re.sub(pattern, '', actual), re.sub(pattern, '', original))
        theme.atomic_state(b'{"theme":"sage-green"}')
        path = theme.prompt_config()
        self.assertEqual(path.read_bytes(), theme.prompt_text('sage-green'))
        path.write_text('broken', encoding='utf-8')
        self.assertEqual(theme.prompt_config().read_bytes(), theme.prompt_text('sage-green'))
        theme.atomic_state(b'{')
        self.assertEqual(theme.prompt_config().read_bytes(), theme.prompt_text(theme.DEFAULT))


if __name__ == '__main__':
    unittest.main()
