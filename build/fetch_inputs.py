# ----------------------------------------------------------------------------------------------------------------------
# Roster-5 Satellite Live Viewer
# fetch_inputs.py - downloads the raw inputs: amateur-observed element sets, CelesTrak catalog, GPS elements, Wikipedia launch list, coastlines
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
"""Download fresh inputs into data/: amateur TLEs, the CelesTrak catalog, the Wikipedia launch list and the land geometry."""
import io, json, os, sys, urllib.request, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
UA = {'User-Agent': 'nro-orbit-watch-build/1.0 (local hobby project)'}

def get(url):
    print('fetching', url)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()

z = zipfile.ZipFile(io.BytesIO(get('https://www.mmccants.org/tles/classfd.zip')))
tle = z.read('classfd.tle').decode('latin1').replace('\r', '')
open(os.path.join(DATA, 'classfd.tle'), 'w', encoding='latin1', newline='\n').write(tle)

open(os.path.join(DATA, 'satcat.csv'), 'wb').write(get('https://celestrak.org/pub/satcat.csv'))
open(os.path.join(DATA, 'gps.tle'), 'wb').write(get('https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle'))

wiki = get('https://en.wikipedia.org/w/api.php?action=parse&page=List_of_NRO_launches&prop=wikitext&format=json&formatversion=2')
open(os.path.join(DATA, 'nro_wikitext.json'), 'wb').write(wiki)

if not os.path.exists(os.path.join(DATA, 'land110.json')):
    open(os.path.join(DATA, 'land110.json'), 'wb').write(get('https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/land-110m.json'))
if not os.path.exists(os.path.join(DATA, 'countries110.json')):
    open(os.path.join(DATA, 'countries110.json'), 'wb').write(get('https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json'))
print('done')
