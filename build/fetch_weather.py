# ----------------------------------------------------------------------------------------------------------------------
# Roster-5 Satellite Live Viewer
# fetch_weather.py - GOES imagery, NWS forecast, hourly outlook and alerts snapshot for the weather slide
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
"""Weather snapshot for the lobby show -> data/weather.json and site/img/goes-fd.jpg.

Live sources (no keys): the latest GOES-East full-disk GeoColor image from NOAA STAR, the National Weather Service forecast
for the HQ grid point, active NWS alerts near HQ, and the national list of Extreme/Severe alerts (hurricanes, tornado
emergencies, blizzards and the like) so the slide can call out the events that matter today. The page tries the same
sources live and falls back to this snapshot when it cannot reach them.
"""
import io, json, os, re, datetime, urllib.request, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data'); IMG = os.path.join(ROOT, 'site', 'img')
UA = {'User-Agent': 'nro-orbit-watch-build/1.0 (local hobby project; contact via github chadburge)', 'Accept': 'application/geo+json, image/jpeg, */*'}
HQ = (39.96683, -105.08874)
GOES = 'https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/GEOCOLOR/1808x1808.jpg'

def get(url, binary=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
        b = r.read(); return b if binary else json.loads(b.decode('utf-8'))

out = {'asof': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'goes': GOES}
try:
    from PIL import Image
    im = Image.open(io.BytesIO(get(GOES, True))).convert('RGB'); im.thumbnail((1400, 1400)); os.makedirs(IMG, exist_ok=True)
    im.save(os.path.join(IMG, 'goes-fd.jpg'), quality=82, optimize=True, progressive=True); out['goesFile'] = 'img/goes-fd.jpg'; print('GOES image saved', im.size)
except Exception as e: print('GOES image failed', e)
try:
    pt = get('https://api.weather.gov/points/%.4f,%.4f' % HQ)['properties']
    fc = get(pt['forecast'])['properties']
    out['forecast'] = {'updated': fc.get('updateTime') or fc.get('updated'), 'periods': [{'name': p['name'], 'temp': p['temperature'], 'unit': p['temperatureUnit'], 'short': p['shortForecast'], 'wind': p.get('windSpeed'), 'dir': p.get('windDirection'), 'detail': (p.get('detailedForecast') or '')[:220], 'day': p.get('isDaytime'), 'icon': p.get('icon')} for p in fc['periods'][:6]]}
    print('forecast ok', out['forecast']['periods'][0])
    hr = get(pt['forecastHourly'])['properties']['periods'][:24]
    out['hourly'] = [{'t': p['startTime'][:16], 'temp': p['temperature'], 'pop': (p.get('probabilityOfPrecipitation') or {}).get('value') or 0, 'wind': p.get('windSpeed'), 'short': p['shortForecast']} for p in hr]
    print('hourly ok', len(out['hourly']))
except Exception as e: print('forecast failed', e)
try:
    al = get('https://api.weather.gov/alerts/active?point=%.4f,%.4f' % HQ)['features']
    out['localAlerts'] = [{'event': a['properties']['event'], 'headline': a['properties'].get('headline'), 'severity': a['properties'].get('severity'), 'ends': a['properties'].get('ends')} for a in al]
    print('local alerts', len(al))
except Exception as e: print('local alerts failed', e)
try:
    nat = get('https://api.weather.gov/alerts/active?severity=Extreme,Severe')['features']
    cnt = collections.Counter(a['properties']['event'] for a in nat)
    # the headline events worth a lobby slide, with where they apply
    keep = re.compile(r'Hurricane|Tropical Storm|Tornado|Blizzard|Ice Storm|Winter Storm Warning|Flash Flood Emergency|Flood Warning|Red Flag|Extreme Wind|High Wind Warning|Excessive Heat|Extreme Cold|Storm Surge|Tsunami|Dust Storm|Fire Warning|Avalanche', re.I)
    areas = collections.defaultdict(set)
    for a in nat:
        p = a['properties']
        if keep.search(p['event']): areas[p['event']].add((p.get('areaDesc') or '').split(';')[0].strip()[:40])
    out['national'] = {'count': len(nat), 'events': [{'event': k, 'count': cnt[k], 'areas': sorted(v)[:6]} for k, v in sorted(areas.items(), key=lambda kv: -cnt[kv[0]])][:8]}
    print('national severe', len(nat), cnt.most_common(5))
except Exception as e: print('national alerts failed', e)
json.dump(out, open(os.path.join(DATA, 'weather.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote data/weather.json')
