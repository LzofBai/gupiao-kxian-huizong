# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
用于将基金估值与K线监控系统打包为可执行程序
"""

import os

# 项目根目录
PROJECT_DIR = os.path.abspath('.')

a = Analysis(
    ['web_server.py'],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=[
        # Flask模板文件
        ('templates', 'templates'),
        # 配置文件
        ('config', 'config'),
    ],
    hiddenimports=[
        # 项目内部模块
        'api',
        'api.FundValuationAPI',
        'api.KLineAPI',
        'database',
        'database.FundDatabase',
        'scripts',
        'scripts.txt2str',
        'utils',
        'utils.Logger',
        'utils.errors',
        'utils.IndexDescription',
        'utils.rate_limiter',
        # Flask相关
        'flask',
        'flask.json',
        'jinja2',
        'jinja2.ext',
        'markupsafe',
        'werkzeug',
        'werkzeug.serving',
        'werkzeug.debug',
        # 其他依赖
        'requests',
        'chardet',
        'sqlite3',
        'json',
        'threading',
        'signal',
        'logging',
        'logging.handlers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='基金K线监控系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='基金K线监控系统',
)
