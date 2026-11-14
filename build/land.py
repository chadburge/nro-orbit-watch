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
