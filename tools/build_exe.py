# ----------------------------------------------------------------------------------------------------------------------
# Roster-5 Satellite Live Viewer
# build_exe.py - packages the viewer as a Windows app folder that needs no Python installation
#
# Author:        Chad Burge
# Created:       2026-11-15
# Repository:    github.com/chadburge/nro-orbit-watch (private) - working copy C:\Users\chadd\dev\nro-orbit-watch
# Project:       a live and historical 3D/2D viewer of U.S. reconnaissance satellites built from public data, with a
#                wall-display "lobby" show customised for Roster-5 Software (Louisville, Colorado)
# Ownership:     Copyright (c) 2026 Chad Burge. All rights reserved. This code and its data pipeline are my own work;
#                any use, copying or redistribution requires my written permission (see LICENSE).
# ----------------------------------------------------------------------------------------------------------------------
"""python tools/build_exe.py  ->  dist-exe/Roster-5 Satellite Live Viewer/ (one .exe plus _internal with site, data, build).

Requires `pip install pyinstaller`. Zip the output folder to share it; the recipient double-clicks the .exe and the
viewer opens in their browser at http://localhost:8787 with the nightly data refresh working exactly as in `python run.py`.
"""
import os
import PyInstaller.__main__
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
A = lambda *p: os.path.join(ROOT, *p)   # absolute paths: with --specpath, relative data paths would resolve against the spec folder
PyInstaller.__main__.run(['--noconfirm', '--onedir', '--name', 'Roster-5 Satellite Live Viewer', '--icon', A('site', 'img', 'r5.ico'),
    '--workpath', A('.pyi-build'), '--specpath', A('.pyi-build'), '--distpath', A('dist-exe'),
    '--add-data', A('site') + os.pathsep + 'site', '--add-data', A('data') + os.pathsep + 'data', '--add-data', A('build') + os.pathsep + 'build',
    '--exclude-module', 'playwright', '--exclude-module', 'tkinter', A('run.py')])
print('packaged into', os.path.join(ROOT, 'dist-exe', 'Roster-5 Satellite Live Viewer'))
