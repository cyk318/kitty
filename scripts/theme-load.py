#!/usr/bin/env python3
"""由 Kitty 内置 Python 执行；状态异常时保留静态紫色兜底。"""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name('theme.py')))['emit']()
