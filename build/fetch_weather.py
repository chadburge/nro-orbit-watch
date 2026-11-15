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
# the other public eyes on the planet, for the "Earth right now" slide: GOES-West, the GOES-East regional scan, Himawari-9 and
# NASA's DSCOVR EPIC camera at L1. Each gets a snapshot file plus the live URL the page tries first.
def save(url, name, size=1400):
    from PIL import Image
    im = Image.open(io.BytesIO(get(url, True))).convert('RGB'); im.thumbnail((size, size)); im.save(os.path.join(IMG, name), quality=82, optimize=True, progressive=True); return 'img/' + name
earth = {'goesEast': {'live': GOES, 'file': out.get('goesFile', 'img/goes-fd.jpg')}}
for key, url, name, size in [('goesWest', 'https://cdn.star.nesdis.noaa.gov/GOES18/ABI/FD/GEOCOLOR/1808x1808.jpg', 'goes-west.jpg', 1400), ('conus', 'https://cdn.star.nesdis.noaa.gov/GOES19/ABI/CONUS/GEOCOLOR/2500x1500.jpg', 'goes-conus.jpg', 1800), ('himawari', 'https://www.data.jma.go.jp/mscweb/data/himawari/img/fd_/fd__trm_0000.jpg', 'himawari.jpg', 1400)]:
    try: earth[key] = {'live': url, 'file': save(url, name, size)}; print(key, 'saved')
    except Exception as e: print(key, 'failed', e)
try:
    ep = get('https://epic.gsfc.nasa.gov/api/natural')[-1]; d = ep['date'][:10].replace('-', '/')
    url = 'https://epic.gsfc.nasa.gov/archive/natural/%s/jpg/%s.jpg' % (d, ep['image'])
    earth['epic'] = {'file': save(url, 'epic.jpg', 1400), 'time': ep['date'][:16] + ' UTC', 'caption': ep.get('caption', '')}; print('epic saved', ep['date'])
except Exception as e: print('epic failed', e)
# the same planet at other wavelengths, for the infrared / radar / spectral variants of the slide:
#   thermal infrared and water vapour from GOES and Himawari (live URLs plus snapshots), ground radar from the NWS,
#   spaceborne radar (Sentinel-1 synthetic aperture radar, served by NASA's OPERA project through GIBS), satellite
#   precipitation (GPM IMERG), VIIRS night lights, MODIS land surface temperature and short-wave infrared false colour
#   (all NASA Worldview snapshots), and NASA EMIT hyperspectral examples from the NASA image library.
def gibs(layer, date, bbox, w, h):
    # Worldview snapshot service; BBOX is latitude first (south, west, north, east)
    return get('https://wvs.earthdata.nasa.gov/api/v1/snapshot?REQUEST=GetSnapshot&LAYERS=%s&CRS=EPSG:4326&TIME=%s&WRAP=day&BBOX=%s&FORMAT=image/jpeg&WIDTH=%d&HEIGHT=%d' % (layer, date, bbox, w, h), True)
def lit(b):
    from PIL import Image
    im = Image.open(io.BytesIO(b)).convert('RGB').resize((120, 60)); px = list(im.getdata()); return sum(1 for q in px if max(q) > 24) / len(px)
def best_gibs(layer, bbox, w, h, days, name):
    """newest day with the most coverage (swath products cover a given area only every few days)"""
    from PIL import Image
    best = None
    for k in range(1, days + 1):
        d = (datetime.date.today() - datetime.timedelta(days=k)).isoformat()
        try: b = get_gibs = gibs(layer, d, bbox, w, h); f = lit(b)
        except Exception as e: print('  gibs', layer[:30], d, 'failed', e); continue
        if best is None or f > best[1] + 0.05: best = (b, f, d)
        if f > 0.6: break
    if not best or best[1] < 0.03: raise RuntimeError('no usable %s in the last %d days' % (layer, days))
    im = Image.open(io.BytesIO(best[0])).convert('RGB'); im.save(os.path.join(IMG, name), quality=84, optimize=True); return {'file': 'img/' + name, 'time': best[2], 'coverage': round(best[1], 2)}
def save_any(url, name, size=1400):
    from PIL import Image
    im = Image.open(io.BytesIO(get(url, True))).convert('RGB'); im.thumbnail((size, size)); im.save(os.path.join(IMG, name), quality=84, optimize=True); return 'img/' + name
CONUS = '24,-126,50,-66'; FRONT_RANGE = '36.5,-109,42,-101.5'
bands = {'infrared': [], 'radar': [], 'spectral': []}
for key, url, name in [('goesEastIR', 'https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/13/1808x1808.jpg', 'goes-east-ir.jpg'), ('goesWestIR', 'https://cdn.star.nesdis.noaa.gov/GOES18/ABI/FD/13/1808x1808.jpg', 'goes-west-ir.jpg'), ('himawariIR', 'https://www.data.jma.go.jp/mscweb/data/himawari/img/fd_/fd__b13_0000.jpg', 'himawari-ir.jpg'), ('goesWV', 'https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/08/1808x1808.jpg', 'goes-wv.jpg')]:
    try: bands['infrared'].append({'key': key, 'live': url, 'file': save_any(url, name)}); print(key, 'saved')
    except Exception as e: print(key, 'failed', e)
try: bands['radar'].append(dict(key='sar', **best_gibs('OPERA_L2_Radiometric_Terrain_Corrected_SAR_Sentinel-1', FRONT_RANGE, 1200, 880, 8, 'sar-front-range.jpg'))); print('sar saved')
except Exception as e: print('sar failed', e)
for key, url, name in [('nwsRadar', 'https://radar.weather.gov/ridge/standard/CONUS_0.gif', 'radar-conus.jpg'), ('kftg', 'https://radar.weather.gov/ridge/standard/KFTG_0.gif', 'radar-denver.jpg')]:
    try: bands['radar'].append({'key': key, 'live': url, 'file': save_any(url, name)}); print(key, 'saved')
    except Exception as e: print(key, 'failed', e)
try: bands['radar'].append(dict(key='imerg', **best_gibs('IMERG_Precipitation_Rate', CONUS, 1200, 520, 3, 'imerg-conus.jpg'))); print('imerg saved')
except Exception as e: print('imerg failed', e)
for key, layer, days, name in [('dnb', 'VIIRS_NOAA20_DayNightBand_At_Sensor_Radiance', 3, 'viirs-night-conus.jpg'), ('lst', 'MODIS_Terra_Land_Surface_Temp_Day', 3, 'modis-lst-conus.jpg'), ('swir', 'MODIS_Terra_CorrectedReflectance_Bands721', 2, 'modis-swir-conus.jpg')]:
    try: bands['spectral'].append(dict(key=key, **best_gibs(layer, CONUS, 1200, 520, days, name))); print(key, 'saved')
    except Exception as e: print(key, 'failed', e)
for key, pid, name in [('emit', 'PIA25427', 'emit-cube.jpg'), ('emit2', 'PIA26417', 'emit-amazon.jpg')]:
    path = os.path.join(IMG, name)
    try:
        if not os.path.exists(path):
            files = [f['href'] for f in get('https://images-api.nasa.gov/asset/' + pid)['collection']['items']]
            save_any(next((u for u in files if u.endswith('~large.jpg')), next((u for u in files if u.endswith('~orig.jpg')), files[0])), name, 1600)
        bands['spectral'].append({'key': key, 'file': 'img/' + name, 'id': pid}); print(key, 'ready')
    except Exception as e: print(key, 'failed', e)
earth['bands'] = bands
out['earth'] = earth
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
