# ----------------------------------------------------------------------------------------------------------------------
# Roster-5 Satellite Live Viewer
# fetch_launches.py - snapshots recent and upcoming launches worldwide from Launch Library 2
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
"""Snapshot recent and upcoming launches worldwide from The Space Devs Launch Library 2 into data/launches.json."""
import json, os, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'nro-orbit-watch-build/1.0 (local hobby project)'}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
        return json.loads(r.read().decode('utf-8'))
def compact(l):
    m = l.get('mission') or {}; pad = l.get('pad') or {}; loc = pad.get('location') or {}; prov = l.get('launch_service_provider') or {}; rk = (l.get('rocket') or {}).get('configuration') or {}
    return {'name': l.get('name'), 'net': l.get('net'), 'status': (l.get('status') or {}).get('abbrev'), 'provider': prov.get('name'), 'rocket': rk.get('full_name') or rk.get('name'),
            'pad': pad.get('name'), 'location': loc.get('name'), 'country': loc.get('country_code'), 'orbit': ((m.get('orbit') or {}).get('abbrev')), 'type': m.get('type'),
            'desc': (m.get('description') or '')[:360], 'nro': 'NRO' in (l.get('name') or '') or 'NROL' in (m.get('name') or '') or 'reconnaissance' in (m.get('description') or '').lower()}
out = {}
for k, u in [('previous', 'https://ll.thespacedevs.com/2.2.0/launch/previous/?limit=40&mode=detailed'), ('upcoming', 'https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=40&mode=detailed')]:
    try:
        out[k] = [compact(l) for l in get(u)['results']]
        print(k, len(out[k]))
    except Exception as e:
        print('ERR', k, e); out[k] = []
import datetime; out['asof'] = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
json.dump(out, open(os.path.join(ROOT, 'data', 'launches.json'), 'w', encoding='utf-8'), ensure_ascii=False)
