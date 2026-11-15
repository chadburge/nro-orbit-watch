# ----------------------------------------------------------------------------------------------------------------------
# Roster-5 Satellite Live Viewer
# build_page.py - embeds data.json and the vendored libraries into the template to produce the local site and the hosted build
#
# Author:        Chad Burge
# Created:       2026-11-14 (first version); this file last reworked 2026-11-15
# Repository:    github.com/chadburge/nro-orbit-watch (private) - working copy C:\Users\chadd\dev\nro-orbit-watch
# Project:       a live and historical 3D/2D viewer of U.S. reconnaissance satellites built from public data, with a
#                wall-display "lobby" show customised for Roster-5 Software (Louisville, Colorado)
# Pipeline:      build/fetch_*.py download inputs -> build/*.py shape them -> build_data.py merges data/data.json ->
#                build_page.py embeds it in build/template.html -> site/index.html (local) and dist/ (hosted copy)
# Ownership:     Copyright (c) 2026 Chad Burge. All rights reserved. This code and its data pipeline are my own work;
#                any use, copying or redistribution requires my written permission (see LICENSE).
# ----------------------------------------------------------------------------------------------------------------------
"""Render site/index.html (local build) and nro-orbit-watch.html (artifact build) from the template and data/data.json."""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tpl = open(os.path.join(ROOT, 'build', 'template.html'), encoding='utf-8').read()
data = json.load(open(os.path.join(ROOT, 'data', 'data.json'), encoding='utf-8'))
js = json.dumps(data, separators=(',', ':')).replace('</', '<\\/')
page = tpl.replace('/*__DATA__*/', 'window.NRO_DATA=' + js + ';')

# artifact build keeps the CDN script tags; the local build uses vendored copies and a full document skeleton
os.makedirs(os.path.join(ROOT, 'dist'), exist_ok=True)
open(os.path.join(ROOT, 'dist', 'nro-orbit-watch.html'), 'w', encoding='utf-8').write(page)

local = page.replace('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js', 'vendor/three.min.js')
local = local.replace('https://cdn.jsdelivr.net/npm/satellite.js@5.0.0/dist/satellite.min.js', 'vendor/satellite.min.js')
local = ('<!doctype html>\n<html lang="en">\n<head>\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
         '<style>:root{color-scheme:dark}html,body{margin:0}img{max-width:100%}</style>\n' + local)
# the template starts with <meta charset> and <title>, then <style>, then markup; close head before the first body element
local = local.replace('<div id="app">', '</head>\n<body>\n<div id="app">', 1) + '\n</body>\n</html>\n'
open(os.path.join(ROOT, 'site', 'index.html'), 'w', encoding='utf-8').write(local)
print('wrote site/index.html and dist/nro-orbit-watch.html', len(local))
