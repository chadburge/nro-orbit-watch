# ----------------------------------------------------------------------------------------------------------------------
# Roster-5 Satellite Live Viewer
# fetch_images.py - searches Wikimedia Commons for free-licensed program and vehicle photographs
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
"""Find public-domain / free-license historical images on Wikimedia Commons for the lobby show and save them to site/img/.
Writes data/images.json with file, title, author, license and a credit line for on-screen attribution."""
import json, os, re, sys, urllib.parse, urllib.request, io
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'site', 'img'); os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'nro-orbit-watch-build/1.0 (local hobby project; contact via github chadburge)'}
API = 'https://commons.wikimedia.org/w/api.php'

# key -> (search query, keywords that must appear in title/description, max results to try)
WANT = {
    'corona': ('CORONA KH-4 reconnaissance satellite', ['corona', 'kh-4', 'discoverer']),
    'discoverer-capsule': ('Discoverer 14 capsule recovery', ['discoverer', 'capsule', 'recovery']),
    'gambit': ('KH-7 Gambit satellite', ['gambit', 'kh-7', 'kh-8']),
    'hexagon': ('KH-9 Hexagon satellite', ['hexagon', 'kh-9']),
    'hexagon-camera': ('Hexagon KH-9 camera film', ['hexagon', 'kh-9']),
    'kh11': ('KH-11 KENNEN satellite image', ['kh-11', 'kennen', 'kennan']),
    'lacrosse': ('Lacrosse radar satellite NRO', ['lacrosse', 'onyx']),
    'titan4': ('Titan IV launch NROL', ['titan']),
    'titan4b': ('Titan IVB Vandenberg launch', ['titan']),
    'delta4h': ('Delta IV Heavy NROL launch', ['delta iv', 'delta 4', 'delta-iv']),
    'delta4h-vafb': ('Delta IV Heavy Vandenberg SLC-6', ['delta']),
    'atlasv': ('Atlas V NROL launch', ['atlas']),
    'falcon9-nrol': ('Falcon 9 NROL launch', ['falcon', 'nrol']),
    'electron-nrol': ('Electron Rocket Lab NROL', ['electron', 'nrol']),
    'minotaur': ('Minotaur rocket NROL launch', ['minotaur']),
    'nro-hq': ('National Reconnaissance Office headquarters Chantilly', ['reconnaissance', 'chantilly', 'nro']),
    'nro-seal': ('National Reconnaissance Office seal', ['reconnaissance', 'seal', 'nro']),
    'nrol39-patch': ('NROL-39 mission patch octopus', ['nrol', 'patch']),
    'nrol-patch': ('NROL mission patch', ['nrol', 'patch']),
    'vandenberg': ('Vandenberg Space Launch Complex 6', ['vandenberg', 'slc']),
    'cape': ('Cape Canaveral Space Launch Complex 41 Atlas', ['canaveral', 'slc', 'complex']),
    'grab': ('GRAB satellite Galactic Radiation and Background', ['grab']),
    'poppy': ('Poppy satellite NRL', ['poppy']),
    'sr71': ('SR-71 Blackbird NASA', ['sr-71', 'blackbird']),
    'u2': ('U-2 Dragon Lady reconnaissance aircraft', ['u-2']),
    'molniya': ('Molniya orbit diagram', ['molniya']),
    'x37b': ('X-37B Orbital Test Vehicle', ['x-37']),
    'sbirs': ('SBIRS GEO satellite', ['sbirs']),
    'shuttle-sts27': ('STS-27 Atlantis launch', ['sts-27', 'atlantis']),
    'titan3': ('Titan IIIB Agena launch', ['titan']),
    'atlas-agena': ('Atlas Agena launch 1968', ['atlas', 'agena']),
    'starlink': ('Falcon 9 Starlink launch Vandenberg', ['falcon', 'starlink']),
}
OK_LIC = re.compile(r'public domain|pd-|cc0|cc by|attribution', re.I)

import time
def get(url, binary=False):
    for attempt in range(6):
        try:
            time.sleep(1.6)
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read() if binary else json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(8 * (attempt + 1)); continue
            raise
    raise RuntimeError('rate limited')

def search(q):
    u = API + '?action=query&format=json&list=search&srnamespace=6&srlimit=12&srsearch=' + urllib.parse.quote(q + ' filetype:bitmap')
    return [h['title'] for h in get(u)['query']['search']]

def info(title):
    u = API + '?action=query&format=json&prop=imageinfo&iiprop=url|extmetadata|size|mime&iiurlwidth=1400&titles=' + urllib.parse.quote(title)
    pages = get(u)['query']['pages']
    for p in pages.values():
        if 'imageinfo' in p:
            ii = p['imageinfo'][0]; m = ii.get('extmetadata', {})
            g = lambda k: re.sub(r'<[^>]+>', '', m.get(k, {}).get('value', '')).strip()
            return {'title': title, 'url': ii.get('thumburl') or ii['url'], 'w': ii.get('width'), 'h': ii.get('height'), 'mime': ii.get('mime'),
                    'license': g('LicenseShortName'), 'author': g('Artist')[:80], 'desc': g('ImageDescription')[:300], 'credit': g('Credit')[:120]}
    return None

existing = {}
if os.path.exists(os.path.join(ROOT, 'data', 'images.json')):
    existing = {i['key']: i for i in json.load(open(os.path.join(ROOT, 'data', 'images.json'), encoding='utf-8'))}
results = []
only = sys.argv[1:]
for key, (q, kws) in WANT.items():
    if only and key not in only: continue
    if key in existing and os.path.exists(os.path.join(OUT, existing[key]['file'])) and not only:
        results.append(existing[key]); continue
    chosen = None
    try:
        for title in search(q):
            t = title.lower()
            if not any(k in t for k in kws): continue
            inf = info(title)
            if not inf or not inf['mime'] or not inf['mime'].startswith('image/') or 'svg' in inf['mime']: continue
            if not OK_LIC.search(inf['license']): continue
            if (inf['w'] or 0) < 500: continue
            chosen = inf; break
    except Exception as e:
        print('ERR', key, e)
    if not chosen:
        print('none for', key); continue
    try:
        data = get(chosen['url'], binary=True)
        from PIL import Image
        im = Image.open(io.BytesIO(data)).convert('RGB')
        im.thumbnail((1400, 1000))
        fn = key + '.jpg'; im.save(os.path.join(OUT, fn), quality=80, optimize=True, progressive=True)
        results.append({'key': key, 'file': fn, 'title': chosen['title'].replace('File:', ''), 'author': chosen['author'], 'license': chosen['license'], 'desc': chosen['desc'], 'w': im.size[0], 'h': im.size[1]})
        print('OK', key, '<-', chosen['title'], '|', chosen['license'], '|', chosen['author'][:40])
    except Exception as e:
        print('ERR save', key, e)
json.dump(results, open(os.path.join(ROOT, 'data', 'images.json'), 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print(len(results), 'images')
