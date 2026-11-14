"""Headline screening for the lobby show -> data/news.json.

Pulls Google News RSS searches for the kinds of events a lobby audience in the aerospace and intelligence world would want
flagged (airspace and FAA actions, launches, Space Force and NRO news, major natural disasters and national emergencies),
then screens hard for anything political, partisan, violent, salacious or otherwise unsuitable for a company wall.
Only items that pass the screen AND match an "impact" pattern are kept, and the page only shows items younger than 48 hours.
Everything is written with a reason so it can be reviewed; set "approved": false by hand to suppress an item.
"""
import json, os, re, html, datetime, email.utils, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
UA = {'User-Agent': 'nro-orbit-watch-build/1.0 (local hobby project)'}
QUERIES = [
    'FAA "ground stop" OR "groundstop" OR "airspace closed" OR "flights grounded"',
    '"Space Force" OR "National Reconnaissance Office" OR NROL OR "Vandenberg" launch',
    'hurricane OR earthquake OR tsunami OR wildfire OR blizzard "National Weather Service" OR "state of emergency"',
    'NASA OR SpaceX OR "United Launch Alliance" OR "Rocket Lab" launch OR mission',
]
IMPACT = re.compile(r'\b(FAA|ground stop|groundstop|airspace|flights? grounded|nationwide|Space Force|Reconnaissance Office|NROL|Vandenberg|launch|mission|hurricane|earthquake|tsunami|wildfire|blizzard|tornado|flood|state of emergency|evacuat\w*|recall|outage|solar storm|geomagnetic|NASA|SpaceX|Rocket Lab|ULA|Artemis|Starship|ISS)\b', re.I)
BLOCK = re.compile(r'\b(Trump|Biden|Harris|Vance|Congress|Senate|House|Republican\w*|Democrat\w*|GOP|election\w*|vote\w*|ballot|impeach\w*|lawsuit|indict\w*|court|judge|abortion|immigra\w*|border|tariff\w*|shutdown|protest\w*|riot\w*|shooting|shot|killed|murder|dead|death|dies|war|strike\w*|missile attack|Gaza|Israel|Ukraine|Russia|Putin|Iran|China|Taiwan|Hamas|terror\w*|sex\w*|scandal|racis\w*|gender|trans\w*|religio\w*|church|gun\w*|crash kills|opinion|op-ed|editorial)\b', re.I)

def fetch(q):
    u = 'https://news.google.com/rss/search?q=' + urllib.parse.quote(q) + '&hl=en-US&gl=US&ceid=US:en'
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r: s = r.read().decode('utf-8', 'replace')
    items = []
    for it in re.findall(r'<item>(.*?)</item>', s, re.S):
        g = lambda tag: html.unescape(re.sub(r'<!\[CDATA\[|\]\]>', '', (re.search(r'<%s[^>]*>(.*?)</%s>' % (tag, tag), it, re.S) or [None, ''])[1])).strip()
        title, link, pub, src = g('title'), g('link'), g('pubDate'), g('source')
        try: ts = email.utils.parsedate_to_datetime(pub)
        except Exception: continue
        items.append({'title': title, 'link': link, 'date': ts.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'source': src})
    return items

seen, out = set(), []
now = datetime.datetime.now(datetime.timezone.utc)
for q in QUERIES:
    try: items = fetch(q)
    except Exception as e: print('ERR', q[:40], e); continue
    for it in items:
        t = re.sub(r'\s+-\s+[^-]+$', '', it['title'])  # strip the " - Source" suffix Google appends
        key = t.lower()[:70]
        if key in seen: continue
        seen.add(key)
        age_h = (now - datetime.datetime.strptime(it['date'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)).total_seconds() / 3600
        if age_h > 72: continue
        why = None
        m = BLOCK.search(t)
        if m: why = 'screened: "%s"' % m.group(0)
        elif not IMPACT.search(t): why = 'no impact keyword'
        out.append({'id': re.sub(r'[^a-z0-9]+', '-', key)[:60], 'title': t, 'source': it['source'], 'date': it['date'], 'link': it['link'], 'approved': why is None, 'why': why})
# keep manual decisions from the previous run
try:
    prev = {p['id']: p for p in json.load(open(os.path.join(DATA, 'news.json'), encoding='utf-8'))['items']}
    for p in out:
        if p['id'] in prev and prev[p['id']].get('manual'): p['approved'] = prev[p['id']]['approved']; p['manual'] = True
except Exception: pass
out.sort(key=lambda p: p['date'], reverse=True)
FLUFF = re.compile(r'\b(football|NFL|NBA|NHL|MLB|NCAA|band|bands|perform\w*|concert|celebrit\w*|Packers|prospect\w*|TikTok|viral|meme|Congressional|funding|blame\w*|resign\w*|secretary|senator|governor|mayor)\b', re.I)
TOPICS = [('FAA nationwide ground stop', r'ground ?stop|flights? grounded|nationwide (stop|halt|stoppage)|flight (chaos|stoppage)|air travel'), ('Hurricane', r'hurricane'), ('Earthquake', r'earthquake|tsunami'), ('Wildfire', r'wildfire'), ('Winter storm', r'blizzard|winter storm|ice storm'), ('Tornado', r'tornado'), ('Flooding', r'flood'), ('Space Force and NRO', r'Space Force|Reconnaissance Office|NROL'), ('Launch', r'launch|Starship|Artemis|Vulcan|Falcon|Electron|ISS')]
PREF = ['AP News', 'Reuters', 'NPR', 'CBS News', 'ABC News', 'NBC News', 'The New York Times', 'The Washington Post', 'Bloomberg', 'The Wall Street Journal', 'USA Today', 'Axios', 'CNN', 'SpaceNews', 'Space.com', 'NASA', 'Spaceflight Now']
clusters = {}
for p in out:
    if not p['approved'] or FLUFF.search(p['title']): continue
    for name, pat in TOPICS:
        if re.search(pat, p['title'], re.I): clusters.setdefault(name, []).append(p); break
major = []
for name, ps in clusters.items():
    outlets = {p['source'] for p in ps}
    if len(ps) < 5 or len(outlets) < 3 or name in ('Launch', 'Space Force and NRO'): continue   # generic topics are covered by the launch slides
    ranked = sorted(ps, key=lambda p: (PREF.index(p['source']) if p['source'] in PREF else 99, len(p['title'])))
    head = ranked[0]
    major.append({'topic': name, 'headline': head['title'], 'source': head['source'], 'date': head['date'], 'link': head['link'], 'outlets': len(outlets), 'stories': len(ps), 'others': [{'title': p['title'], 'source': p['source']} for p in ranked[1:4]]})
major.sort(key=lambda m: -m['stories'])
print('major stories:', [(m['topic'], m['stories'], m['outlets']) for m in major])
json.dump({'asof': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'items': out, 'major': major}, open(os.path.join(DATA, 'news.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
ok = [p for p in out if p['approved']]
print('%d items, %d approved' % (len(out), len(ok)))
for p in ok[:12]: print('  OK ', p['date'][:10], p['title'][:100])
for p in [p for p in out if not p['approved']][:8]: print('  no ', p['why'], '|', p['title'][:80])
