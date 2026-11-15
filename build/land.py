# ----------------------------------------------------------------------------------------------------------------------
# Roster-5 Satellite Live Viewer
# land.py - converts world-atlas TopoJSON coastlines into the compact polygon rings the page draws
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
import json, sys
import os
d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
t = json.load(open(d + '/land110.json', encoding='utf-8'))
sc, tr = t['transform']['scale'], t['transform']['translate']
arcs = []
for arc in t['arcs']:
    x = y = 0
    pts = []
    for dx, dy in arc:
        x += dx; y += dy
        pts.append((round(x * sc[0] + tr[0], 2), round(y * sc[1] + tr[1], 2)))
    arcs.append(pts)
def ring(idx):
    out = []
    for i in idx:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        if out and out[-1] == a[0]:
            out.extend(a[1:])
        else:
            out.extend(a)
    return out
polys = []
geom = t['objects']['land']
geoms = geom['geometries'] if geom['type'] == 'GeometryCollection' else [geom]
for g in geoms:
    if g['type'] == 'Polygon':
        for r in g['arcs']:
            polys.append(ring(r))
    elif g['type'] == 'MultiPolygon':
        for p in g['arcs']:
            for r in p:
                polys.append(ring(r))
print(len(polys), 'rings', sum(len(p) for p in polys), 'points')
# flatten to [lon,lat,...] per ring
out = [[v for pt in p for v in pt] for p in polys]
json.dump(out, open(d + '/land.json', 'w'), separators=(',', ':'))
import os
print(os.path.getsize(d + '/land.json'))
