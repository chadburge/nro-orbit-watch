"""Per-mission imagery for the lobby show: official NROL mission patches (from the Wikipedia table), a Commons search for
launch photos of each NROL mission, satellite-class photos and period launch vehicles. Appends to data/images.json with tags."""
import json, os, re, sys, time, io, urllib.parse, urllib.request, urllib.error
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data'); OUT = os.path.join(ROOT, 'site', 'img'); os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'nro-orbit-watch-build/1.0 (local hobby project; contact via github chadburge)'}
API = 'https://commons.wikimedia.org/w/api.php'
OK_LIC = re.compile(r'public domain|pd-|cc0|cc by|attribution', re.I)
from PIL import Image

def get(url, binary=False):
    for attempt in range(6):
        try:
            time.sleep(1.5)
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read() if binary else json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(10 * (attempt + 1)); continue
            if e.code == 404: return None
            raise
    return None

def info(title):
    u = API + '?action=query&format=json&prop=imageinfo&iiprop=url|extmetadata|size|mime&iiurlwidth=1400&titles=' + urllib.parse.quote(title)
    j = get(u)
    if not j: return None
    for p in j['query']['pages'].values():
        if 'imageinfo' in p:
            ii = p['imageinfo'][0]; m = ii.get('extmetadata', {})
            g = lambda k: re.sub(r'<[^>]+>', '', m.get(k, {}).get('value', '')).strip()
            return {'title': p['title'], 'url': ii.get('thumburl') or ii['url'], 'w': ii.get('width'), 'h': ii.get('height'), 'mime': ii.get('mime'), 'license': g('LicenseShortName'), 'author': g('Artist')[:80], 'desc': g('ImageDescription')[:300]}
    return None

def search(q, n=10):
    j = get(API + '?action=query&format=json&list=search&srnamespace=6&srlimit=%d&srsearch=' % n + urllib.parse.quote(q + ' filetype:bitmap'))
    return [h['title'] for h in j['query']['search']] if j else []

def save(key, inf, maxw=1400):
    data = get(inf['url'], binary=True)
    im = Image.open(io.BytesIO(data)).convert('RGB'); im.thumbnail((maxw, 1000))
    fn = key + '.jpg'; im.save(os.path.join(OUT, fn), quality=80, optimize=True, progressive=True)
    return {'key': key, 'file': fn, 'title': inf['title'].replace('File:', ''), 'author': inf['author'], 'license': inf['license'], 'desc': inf['desc'], 'w': im.size[0], 'h': im.size[1]}

images = json.load(open(os.path.join(DATA, 'images.json'), encoding='utf-8'))
have = {i['key']: i for i in images}
def add(entry, tags):
    entry.update(tags); have[entry['key']] = entry
    json.dump(list(have.values()), open(os.path.join(DATA, 'images.json'), 'w', encoding='utf-8'), indent=0, ensure_ascii=False)

rows = json.load(open(os.path.join(DATA, 'nrol.json'), encoding='utf-8'))
mode = sys.argv[1] if len(sys.argv) > 1 else 'all'

# 1. mission patches (official NRO artwork, public domain as U.S. government works)
if mode in ('all', 'patches'):
    for r in rows:
        pf = r.get('patchFile'); nrol = r['nrol'].split(' ')[0]
        key = 'patch-' + nrol.lower()
        if not pf or key in have: continue
        try:
            inf = info('File:' + pf)
            if not inf or not inf['mime'] or not inf['mime'].startswith('image/'): print('no patch', nrol); continue
            e = save(key, inf, 900); add(e, {'kind': 'patch', 'nrol': nrol}); print('PATCH', nrol, inf['license'])
        except Exception as ex: print('ERR patch', nrol, ex)

# 2. launch photos per mission
if mode in ('all', 'launches'):
    for r in rows:
        nrol = r['nrol'].split(' ')[0]; key = 'launch-' + nrol.lower()
        if key in have or r['status'] in ('Awaiting launch', 'Canceled', ''): continue
        try:
            best = None
            for t in search(nrol + ' launch', 8):
                tl = t.lower().replace('_', ' ')
                if nrol.lower() not in tl: continue
                if 'patch' in tl or 'logo' in tl or 'insignia' in tl: continue
                inf = info(t)
                if not inf or not inf['mime'].startswith('image/') or 'svg' in inf['mime'] or not OK_LIC.search(inf['license']) or (inf['w'] or 0) < 600: continue
                best = inf; break
            if best: e = save(key, best); add(e, {'kind': 'launch', 'nrol': nrol, 'rocket': r['rocket']}); print('LAUNCH', nrol, '<-', best['title'][:60], '|', best['license'])
            else: print('no launch photo', nrol)
        except Exception as ex: print('ERR launch', nrol, ex)

# 3. satellite-class and vehicle images
CLASS = {
    'sat-corona': ('KH-4B Corona satellite camera museum', ['corona', 'kh-4'], {'kind': 'satellite', 'family': 'CORONA'}),
    'sat-hexagon': ('KH-9 Hexagon satellite museum Udvar-Hazy', ['hexagon', 'kh-9'], {'kind': 'satellite', 'family': 'HEXAGON'}),
    'sat-gambit3': ('KH-8 Gambit 3 satellite museum', ['gambit', 'kh-8'], {'kind': 'satellite', 'family': 'GAMBIT'}),
    'sat-grab': ('GRAB satellite National Reconnaissance', ['grab'], {'kind': 'satellite', 'family': 'GRAB'}),
    'sat-poppy': ('Poppy satellite Naval Research Laboratory', ['poppy'], {'kind': 'satellite', 'family': 'POPPY'}),
    'sat-igs': ('IGS Information Gathering Satellite Japan', ['igs', 'information gathering'], {'kind': 'satellite', 'family': 'IGS'}),
    'sat-sarlupe': ('SAR-Lupe satellite model', ['sar-lupe', 'sar lupe'], {'kind': 'satellite', 'family': 'SAR-Lupe'}),
    'sat-cso': ('CSO satellite Composante Spatiale Optique', ['cso'], {'kind': 'satellite', 'family': 'CSO'}),
    'sat-ofeq': ('Ofeq satellite Israel', ['ofeq', 'ofek'], {'kind': 'satellite', 'family': 'Ofeq'}),
    'sat-dsp': ('Defense Support Program satellite', ['dsp', 'defense support'], {'kind': 'satellite', 'family': 'Defense Support Program'}),
    'sat-stss': ('STSS Space Tracking and Surveillance System satellite', ['stss'], {'kind': 'satellite', 'family': 'Space Tracking and Surveillance System'}),
    'sat-hubble': ('Hubble Space Telescope in orbit', ['hubble'], {'kind': 'similar', 'family': 'KH-11'}),
    'sat-tdrs': ('TDRS satellite deployment', ['tdrs'], {'kind': 'similar', 'family': 'Quasar / SDS'}),
    'sat-molniya': ('Molniya satellite model', ['molniya'], {'kind': 'similar', 'family': 'Jumpseat'}),
    'veh-titan3b': ('Titan IIIB launch Vandenberg', ['titan'], {'kind': 'vehicle', 'rocket': 'Titan III', 'era': [1966, 1987]}),
    'veh-titan3d': ('Titan IIID launch', ['titan'], {'kind': 'vehicle', 'rocket': 'Titan III', 'era': [1971, 1982]}),
    'veh-titan34d': ('Titan 34D launch', ['titan'], {'kind': 'vehicle', 'rocket': 'Titan 34', 'era': [1982, 1989]}),
    'veh-titan3c': ('Titan IIIC launch Cape Canaveral', ['titan'], {'kind': 'vehicle', 'rocket': 'Titan III', 'era': [1965, 1982]}),
    'veh-atlas-agena': ('Atlas Agena D launch 1960s', ['atlas'], {'kind': 'vehicle', 'rocket': 'Atlas', 'era': [1960, 1978]}),
    'veh-atlas2': ('Atlas IIAS launch Cape Canaveral', ['atlas'], {'kind': 'vehicle', 'rocket': 'Atlas II', 'era': [1991, 2004]}),
    'veh-atlas3': ('Atlas IIIB launch', ['atlas'], {'kind': 'vehicle', 'rocket': 'Atlas III', 'era': [2000, 2005]}),
    'veh-minotaur4': ('Minotaur IV launch Wallops', ['minotaur'], {'kind': 'vehicle', 'rocket': 'Minotaur IV', 'era': [2010, 2030]}),
    'veh-electron': ('Electron rocket launch Mahia', ['electron'], {'kind': 'vehicle', 'rocket': 'Electron', 'era': [2017, 2030]}),
    'veh-taurus': ('Taurus rocket launch Vandenberg', ['taurus'], {'kind': 'vehicle', 'rocket': 'Taurus', 'era': [1994, 2011]}),
    'veh-delta2': ('Delta II launch Vandenberg', ['delta'], {'kind': 'vehicle', 'rocket': 'Delta II', 'era': [1989, 2018]}),
    'veh-atlasf': ('Atlas F launch Vandenberg', ['atlas'], {'kind': 'vehicle', 'rocket': 'Atlas F', 'era': [1965, 1995]}),
    'veh-shuttle': ('Space Shuttle launch Discovery', ['shuttle', 'sts'], {'kind': 'vehicle', 'rocket': 'Space Shuttle', 'era': [1981, 2011]}),
    # specific events and places used by fact cards
    'ev-titan4a-1998': ('Titan IVA-20 explosion 1998 Cape Canaveral', ['titan iv', 'titan 4', 'a-20', 'k-17'], {'kind': 'event', 'fact': 'A failure 40 seconds in'}),
    'ev-sts36': ('STS-36 launch Atlantis 1990', ['sts-36', 'sts 36'], {'kind': 'event', 'fact': 'The satellite that went missing'}),
    'ev-usa193': ('USS Lake Erie SM-3 launch USA-193 February 2008', ['lake erie', 'sm-3', 'usa-193', 'usa 193'], {'kind': 'event', 'fact': 'USA 193: shot down on purpose'}),
    'nro-hq': ('National Reconnaissance Office headquarters Chantilly Virginia building', ['nro', 'reconnaissance office'], {'kind': 'place', 'fact': 'Eleven agencies, one office'}),
    # topic illustrations for the headlines slide and a night-sky photo for the passes slide
    'news-aviation': ('Denver International Airport control tower aircraft', ['denver', 'dia'], {'kind': 'news'}),
    'news-hurricane': ('hurricane from space GOES satellite image', ['hurricane'], {'kind': 'news'}),
    'news-earthquake': ('earthquake damage street USGS', ['earthquake'], {'kind': 'news'}),
    'news-wildfire': ('wildfire smoke plume satellite image MODIS', ['fire', 'smoke'], {'kind': 'news'}),
    'news-winter': ('blizzard snowstorm satellite image NASA', ['snow', 'blizzard', 'winter'], {'kind': 'news'}),
    'news-tornado': ('tornado supercell NOAA photo', ['tornado'], {'kind': 'news'}),
    'news-flood': ('flooding aerial photograph river', ['flood'], {'kind': 'news'}),
    'sky-pass': ('satellite trail long exposure night sky stars', ['satellite', 'trail', 'pass'], {'kind': 'news'}),
}
if mode in ('all', 'class'):
    for key, (q, kws, tags) in CLASS.items():
        if key in have: continue
        try:
            best = None
            for t in search(q, 10):
                tl = t.lower().replace('_', ' ')
                if not any(k in tl for k in kws): continue
                inf = info(t)
                if not inf or not inf['mime'].startswith('image/') or 'svg' in inf['mime'] or not OK_LIC.search(inf['license']) or (inf['w'] or 0) < 500: continue
                best = inf; break
            if best: e = save(key, best); add(e, tags); print('CLASS', key, '<-', best['title'][:60], '|', best['license'])
            else: print('none', key)
        except Exception as ex: print('ERR class', key, ex)
print('total images', len(have))
