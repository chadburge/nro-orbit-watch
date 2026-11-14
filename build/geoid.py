"""EGM96 geoid undulation grid for the gravity slide -> data/geoid.json (2-degree grid, metres above the WGS84 ellipsoid).

Source: the NGA EGM96 15-minute geoid as distributed with PROJ (us_nga_egm96_15.tif, public domain). The file is downloaded
on demand into data/ and ignored by git. The lobby exaggerates the undulations (about -106 m to +85 m) thousands of times
to show where gravity pulls the sea surface up or down.
"""
import json, os, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data'); TIF = os.path.join(DATA, 'egm96_15.tif')
if not os.path.exists(TIF):
    print('downloading EGM96 grid')
    with urllib.request.urlopen(urllib.request.Request('https://raw.githubusercontent.com/OSGeo/PROJ-data/master/us_nga/us_nga_egm96_15.tif', headers={'User-Agent': 'nro-orbit-watch-build/1.0'}), timeout=120) as r:
        open(TIF, 'wb').write(r.read())
from PIL import Image
im = Image.open(TIF); W, H = im.size   # 1440 x 721: lon -180..180 step 0.25, lat 90..-90 step 0.25
px = im.load()
STEP = 2
lons = list(range(-180, 181, STEP)); lats = list(range(90, -91, -STEP))
grid = []
for lat in lats:
    row = []
    for lon in lons:
        x = min(W - 1, int(round((lon + 180) / 0.25))); y = min(H - 1, int(round((90 - lat) / 0.25)))
        row.append(round(float(px[x, y]), 1))
    grid.append(row)
flat = [v for r in grid for v in r]
json.dump({'step': STEP, 'lon0': -180, 'lat0': 90, 'cols': len(lons), 'rows': len(lats), 'min': min(flat), 'max': max(flat), 'values': grid},
          open(os.path.join(DATA, 'geoid.json'), 'w'), separators=(',', ':'))
print('geoid grid', len(lats), 'x', len(lons), 'range', min(flat), max(flat))
