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
