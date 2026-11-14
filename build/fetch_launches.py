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
