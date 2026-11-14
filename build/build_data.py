import json, csv, re, sys, datetime, collections
import os
d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# ---------- catalog ----------
sat_by_name, sat_by_id, sat_by_date = {}, {}, collections.defaultdict(list)
with open(d + '/satcat.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        sat_by_name[row['OBJECT_NAME']] = row
        sat_by_id[row['OBJECT_ID']] = row
        sat_by_date[row['LAUNCH_DATE']].append(row)

# ---------- TLEs ----------
tles = {}  # intl designator -> (name, l1, l2)
tle_lines = open(d + '/classfd.tle', encoding='latin1').read().split('\n')
tle_lines = [l for l in tle_lines if l.strip()]
tle_noid = []
for i in range(0, len(tle_lines) - 2, 3):
    name, l1, l2 = tle_lines[i].strip(), tle_lines[i + 1], tle_lines[i + 2]
    des = l1[9:17].strip()
    if des[:2].isdigit():
        yy = int(des[:2]); yr = 1900 + yy if yy > 56 else 2000 + yy
        tles[f"{yr}-{des[2:]}"] = (name, l1, l2)
    else:
        tle_noid.append((name, l1, l2))
print('tles', len(tles), 'without designator', len(tle_noid))

def tle_epoch(l1):
    yy = int(l1[18:20]); yr = 1900 + yy if yy > 56 else 2000 + yy
    doy = float(l1[20:32])
    return (datetime.datetime(yr, 1, 1) + datetime.timedelta(days=doy - 1)).strftime('%Y-%m-%d')

def orbit_class_from_tle(l2):
    inc = float(l2[8:16]); ecc = float('0.' + l2[26:33].strip()); mm = float(l2[52:63])
    period = 1440 / mm
    if ecc > 0.5: return 'HEO / Molniya'
    if period > 1380 and period < 1500: return 'GEO'
    if period > 1500: return 'High orbit'
    if period < 225: return 'LEO'
    return 'MEO'

# ---------- helpers ----------
MONTHS = {m: i for i, m in enumerate(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], 1)}
def parse_date(s):
    m = re.match(r'(\d{1,2}) (\w+) (\d{4})', s)
    if m and m.group(2) in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"
    m = re.search(r'(\d{4})', s)
    return m.group(1) if m else None

def decade_of(date):
    if not date: return None
    return f"{int(date[:4]) // 10 * 10}s"

def norm_status(s):
    s = (s or '').lower()
    if 'presumed active' in s: return 'Active (presumed)'
    if 'status unknown' in s: return 'In orbit, status unknown'
    if 'deorbit' in s or 'decay' in s or 'reenter' in s: return 'Decayed'
    if 'destroyed' in s or 'failed' in s: return 'Launch failure'
    if 'retired' in s: return 'Retired, in orbit'
    if 'await' in s: return 'Awaiting launch'
    if 'cancel' in s: return 'Canceled'
    return 'In orbit, status unknown'

def norm_function(project, function, nrol=''):
    p = (project or '').lower(); f = (function or '').lower()
    if 'kh-11' in p or 'misty' in p or 'optical' in f or 'electro-optical' in f: return 'Optical imaging'
    if 'lacrosse' in p or 'topaz' in p or 'radar' in f or 'sar' in f.split() or f == 'sar': return 'Radar imaging'
    if 'intruder' in p or 'noss' in p or 'naval' in f: return 'Ocean surveillance'
    if 'trumpet' in p or 'mercury' in p or f == 'elint': return 'ELINT (eavesdropping)'
    if 'orion' in p or 'sharp' in p or 'sigint' in f or 'comint' in f or 'telint' in f: return 'SIGINT (eavesdropping)'
    if 'quasar' in p or 'communications' in f or 'geolite' in p: return 'Communications relay'
    if 'silentbarker' in p or 'situational' in f: return 'Space surveillance'
    if 'starshield' in p or 'starshield' in f: return 'Proliferated architecture'
    if nrol == 'NROL-21': return 'Radar imaging'
    return 'Technology / undisclosed'

def norm_orbit(text, tle=None):
    if tle: return orbit_class_from_tle(tle[2])
    t = (text or '').lower()
    if 'molniya' in t: return 'HEO / Molniya'
    if 'gso' in t or 'geo' in t: return 'GEO'
    if 'meo' in t: return 'MEO'
    if 'leo' in t or 'sso' in t or ' km' in t: return 'LEO'
    return 'Unknown'

def owner_for(project, function):
    p = (project or '').lower(); f = (function or '').lower()
    if 'intruder' in p or 'noss' in p or 'naval' in f: return 'NRO / U.S. Navy'
    if 'improved trumpet' in p: return 'NRO / U.S. Space Force (shared)'
    if 'starshield' in p or 'starshield' in f: return 'NRO (SpaceX-built)'
    return 'NRO'

WIKI = {
    'kh-11': 'KH-11_KENNEN', 'misty': 'Misty_(satellite)', 'lacrosse': 'Lacrosse_(satellite)', 'topaz': 'Topaz_(satellite)',
    'orion': 'Orion_(satellite)', 'mentor': 'Orion_(satellite)', 'trumpet': 'Trumpet_(satellite)', 'mercury': 'Mercury_(satellite)',
    'quasar': 'Satellite_Data_System', 'sds': 'Satellite_Data_System', 'intruder': 'Naval_Ocean_Surveillance_System',
    'noss': 'Naval_Ocean_Surveillance_System', 'starshield': 'Starshield', 'silentbarker': 'Silentbarker', 'geolite': 'GeoLITE',
    'stex': 'STEX', 'canyon': 'Canyon_(satellite)', 'rhyolite': 'Rhyolite/Aquacade', 'chalet': 'Chalet_(satellite)', 'vortex': 'Chalet_(satellite)',
    'magnum': 'Magnum_(satellite)', 'jumpseat': 'Jumpseat_(satellite)', 'sharp': 'USA-250', 'rpp': 'USA-225',
}
def wiki_for(program, fallback):
    p = (program or '').lower()
    for k, v in WIKI.items():
        if k in p: return 'https://en.wikipedia.org/wiki/' + v
    return 'https://en.wikipedia.org/w/index.php?search=' + fallback.replace(' ', '+')

def tle_fields(t):
    if not t: return {}
    name, l1, l2 = t
    inc = float(l2[8:16]); ecc = float('0.' + l2[26:33].strip()); mm = float(l2[52:63])
    period = 1440 / mm
    a = (398600.4418 * (period * 60 / (2 * 3.14159265358979)) ** 2) ** (1 / 3)
    return {'tle': [l1, l2], 'tleName': name, 'epoch': tle_epoch(l1), 'inc': round(inc, 1), 'period': round(period, 1),
            'apogee': round(a * (1 + ecc) - 6378.137), 'perigee': round(a * (1 - ecc) - 6378.137)}

objects = []
used_tle = set()

# GPS constellation (CelesTrak gps-ops, public elements) for the navigation explainer; its own layer, off by default
if os.path.exists(d + '/gps.tle'):
    gl = [l for l in open(d + '/gps.tle', encoding='latin1').read().replace('\r', '').split('\n') if l.strip()]
    for i in range(0, len(gl) - 2, 3):
        name, l1, l2 = gl[i].strip(), gl[i + 1], gl[i + 2]
        des = l1[9:17].strip(); cospar = f"{1900 + int(des[:2]) if int(des[:2]) > 56 else 2000 + int(des[:2])}-{des[2:]}"
        s = sat_by_id.get(cospar); prn = re.search(r'PRN (\d+)', name)
        o = {'name': f"GPS {name.split('(')[0].replace('GPS', '').strip()}" + (f" (PRN {prn.group(1)})" if prn else ''), 'program': 'GPS', 'function': 'Navigation', 'kind': 'payload', 'layer': 'gps',
             'owner': 'U.S. Space Force', 'nation': 'United States', 'date': s['LAUNCH_DATE'] if s else cospar[:4] + '-01-01', 'status': 'Active', 'cospar': cospar, 'orbit': 'MEO',
             'notes': 'GPS navigation satellite; public elements from CelesTrak.', 'links': {'wiki': 'https://en.wikipedia.org/wiki/Global_Positioning_System'}, 'rocket': '', 'site': ''}
        o.update(tle_fields((name, l1, l2)))
        if s: o['norad'] = int(s['NORAD_CAT_ID']); o['links']['n2yo'] = f"https://www.n2yo.com/satellite/?s={s['NORAD_CAT_ID']}"
        objects.append(o)
    print('gps', sum(1 for o in objects if o['layer'] == 'gps'))

def add(o):
    o.setdefault('kind', 'payload')
    o.setdefault('layer', 'nro')
    o.setdefault('nation', 'United States')
    o.setdefault('owner', 'NRO')
    o['decade'] = o.get('decade') or decade_of(o.get('date'))
    o['decades'] = o.get('decades') or ([o['decade']] if o['decade'] else [])
    objects.append(o)

# ---------- NROL launches ----------
rows = json.load(open(d + '/nrol.json', encoding='utf-8'))
for r in rows:
    date = parse_date(r['date'])
    nrol = r['nrol'].split(' ')[0]
    status = norm_status(r['status'])
    func = norm_function(r['project'], r['function'], nrol)
    base = {
        'nrol': r['nrol'], 'nick': r['nick'], 'date': date, 'site': r['site'], 'rocket': r['rocket'],
        'program': r['project'] or ('Starshield' if 'Starshield' in r['remarks'] else 'Undisclosed'),
        'function': func, 'status': status, 'orbitText': r['orbit'], 'notes': r['remarks'],
        'owner': owner_for(r['project'], r['function']),
    }
    # payloads from catalog by launch date
    pays = []
    if date and len(date) == 10:
        pays = [s for s in sat_by_date.get(date, []) if s['OBJECT_NAME'].startswith('USA ') and s['OBJECT_TYPE'] == 'PAY']
        if r['usa'] in ('N/A', '', '-'):
            pays = []
    if not pays:
        o = dict(base, name=f"{nrol} payload" if status not in ('Awaiting launch', 'Canceled') else nrol,
                 usa=r['usa'] if r['usa'] not in ('N/A', '-') else None, orbit=norm_orbit(r['orbit']),
                 links={'wiki': wiki_for(r['project'], nrol), 'nrolList': 'https://en.wikipedia.org/wiki/List_of_NRO_launches'})
        if status == 'Launch failure': o['kind'] = 'payload'
        add(o)
        # companion debris for NOSS pairs is handled below via TLE
        continue
    multi = len(pays) > 1
    for s in pays:
        t = tles.get(s['OBJECT_ID'])
        if t: used_tle.add(s['OBJECT_ID'])
        name = s['OBJECT_NAME']
        prog = base['program']
        if multi and 'Intruder' in prog: name = f"{s['OBJECT_NAME']} ({prog.split(' ')[1]}A)"
        o = dict(base, name=name, usa=s['OBJECT_NAME'], norad=int(s['NORAD_CAT_ID']), cospar=s['OBJECT_ID'],
                 orbit=norm_orbit(r['orbit'], t), decayed=s['DECAY_DATE'] or None,
                 links={'wiki': wiki_for(r['project'], s['OBJECT_NAME'].replace('USA ', 'USA-')),
                        'n2yo': f"https://www.n2yo.com/satellite/?s={s['NORAD_CAT_ID']}",
                        'heavens': f"https://heavens-above.com/satinfo.aspx?satid={s['NORAD_CAT_ID']}",
                        'nrolList': 'https://en.wikipedia.org/wiki/List_of_NRO_launches'}, **tle_fields(t))
        if s['DECAY_DATE']: o['status'] = 'Decayed'
        add(o)
    # NOSS companion objects catalogued as debris but tracked as second payload
    for s in sat_by_date.get(date, []):
        if s['OBJECT_NAME'].endswith(' DEB') and s['OBJECT_ID'] in tles and 'Intruder' in base['program']:
            t = tles[s['OBJECT_ID']]; used_tle.add(s['OBJECT_ID'])
            o = dict(base, name=f"{s['OBJECT_NAME'].replace(' DEB','')} ({base['program'].split(' ')[1]}B)", usa=s['OBJECT_NAME'].replace(' DEB', ''),
                     norad=int(s['NORAD_CAT_ID']), cospar=s['OBJECT_ID'], orbit=norm_orbit(r['orbit'], t),
                     notes='Second satellite of the pair; catalogued publicly as debris. ' + base['notes'],
                     links={'wiki': wiki_for(r['project'], 'NOSS'), 'n2yo': f"https://www.n2yo.com/satellite/?s={s['NORAD_CAT_ID']}",
                            'heavens': f"https://heavens-above.com/satinfo.aspx?satid={s['NORAD_CAT_ID']}",
                            'nrolList': 'https://en.wikipedia.org/wiki/List_of_NRO_launches'}, **tle_fields(t))
            add(o)

# ---------- pre-1996 payloads ----------
for h in json.load(open(d + '/hist.json', encoding='utf-8')):
    s = sat_by_id.get(h['cospar'])
    t = tles.get(h['cospar'])
    if t: used_tle.add(h['cospar'])
    status = h['status']
    if status == 'Destroyed': status = 'Launch failure'
    elif status not in ('Retired, in orbit','Decayed','Failed, in orbit'): status = norm_status(status)
    if s and s['DECAY_DATE'] and status != 'Launch failure': status = 'Decayed'
    o = {'name': h['name'], 'program': h['program'], 'function': norm_function(h['program'], h['function']), 'date': h['date'],
         'site': h['site'], 'rocket': h['vehicle'], 'status': status, 'orbitText': h['orbit'], 'notes': h['notes'],
         'usa': h['usa'], 'cospar': h['cospar'], 'orbit': norm_orbit(h['orbit'], t), 'owner': owner_for(h['program'], h['function']),
         'links': {'wiki': wiki_for(h['program'], h['name'])}}
    if s:
        o['norad'] = int(s['NORAD_CAT_ID']); o['catName'] = s['OBJECT_NAME']; o['decayed'] = s['DECAY_DATE'] or None
        o['links']['n2yo'] = f"https://www.n2yo.com/satellite/?s={s['NORAD_CAT_ID']}"
        o['links']['heavens'] = f"https://heavens-above.com/satinfo.aspx?satid={s['NORAD_CAT_ID']}"
    o.update(tle_fields(t))
    add(o)

# ---------- declassified film-return and early ELINT programs (program-level) ----------
PROGRAMS = [
    ('CORONA (KH-1 to KH-4B)', '1959-06-25', '1972-05-25', 145, 'Optical imaging', 'First photo-reconnaissance program; film capsules recovered in mid-air. Declassified 1995.', 'CORONA_(satellite)'),
    ('GRAB', '1960-06-22', '1962-04-26', 5, 'ELINT (eavesdropping)', 'Galactic Radiation and Background: first US reconnaissance satellite, Navy ELINT. Declassified 1998.', 'GRAB_(satellite)'),
    ('ARGON (KH-5)', '1961-02-17', '1964-08-21', 12, 'Optical imaging', 'Mapping camera for geodetic targeting.', 'KH-5_Argon'),
    ('POPPY', '1962-12-13', '1971-12-14', 7, 'ELINT (eavesdropping)', 'Navy ELINT successor to GRAB; multi-satellite launches. Declassified 2005.', 'Poppy_(satellite)'),
    ('LANYARD (KH-6)', '1963-03-18', '1963-07-31', 3, 'Optical imaging', 'Short-lived high-resolution camera program.', 'KH-6_Lanyard'),
    ('GAMBIT-1 (KH-7)', '1963-07-12', '1967-06-04', 38, 'Optical imaging', 'First high-resolution close-look satellite. Declassified 2011.', 'KH-7_Gambit'),
    ('GAMBIT-3 (KH-8)', '1966-07-29', '1984-04-17', 54, 'Optical imaging', 'Close-look imaging to about 10 cm resolution. Declassified 2011.', 'KH-8_Gambit_3'),
    ('HEXAGON (KH-9)', '1971-06-15', '1986-04-18', 20, 'Optical imaging', 'Big Bird wide-area search camera with four film capsules. Declassified 2011.', 'KH-9_Hexagon'),
]
for name, start, end, n, func, notes, wiki in PROGRAMS:
    decs = [f"{y}s" for y in range(int(start[:4]) // 10 * 10, int(end[:4]) // 10 * 10 + 1, 10)]
    add({'kind': 'program', 'name': name, 'program': name, 'function': func, 'date': start, 'endDate': end, 'launches': n,
         'status': 'Program ended, all decayed', 'orbit': 'LEO', 'owner': 'NRO (CIA / Air Force heritage)', 'notes': notes,
         'decade': decs[0], 'decades': decs, 'links': {'wiki': 'https://en.wikipedia.org/wiki/' + wiki}})

# ---------- other objects in the amateur-tracked set ----------
OTHER = [  # prefix, program, function, owner, nation, layer
    ('IGS', 'IGS (Information Gathering Satellite)', None, 'Japan Cabinet Satellite Intelligence Center', 'Japan', 'allied'),
    ('SAR Lupe', 'SAR-Lupe', 'Radar imaging', 'German Bundeswehr', 'Germany', 'allied'),
    ('Sarah', 'SARah', 'Radar imaging', 'German Bundeswehr', 'Germany', 'allied'),
    ('CSO', 'CSO (Composante Spatiale Optique)', 'Optical imaging', 'French DGA / CNES', 'France', 'allied'),
    ('Helios', 'Helios 2', 'Optical imaging', 'French DGA / CNES', 'France', 'allied'),
    ('Ceres', 'CERES', 'ELINT (eavesdropping)', 'French DGA / CNES', 'France', 'allied'),
    ('Ofeq', 'Ofeq', 'Optical imaging', 'Israel Ministry of Defense', 'Israel', 'allied'),
    ('TecSar', 'TecSAR (Ofeq 8)', 'Radar imaging', 'Israel Ministry of Defense', 'Israel', 'allied'),
    ('Optsat', 'OPTSAT-3000', 'Optical imaging', 'Italian Ministry of Defence', 'Italy', 'allied'),
    ('Sicral', 'SICRAL', 'Communications relay', 'Italian Ministry of Defence', 'Italy', 'allied'),
    ('GovSat', 'GovSat-1', 'Communications relay', 'GovSat (Luxembourg / SES)', 'Luxembourg', 'allied'),
    ('DSN', 'DSN (X-band defense comms)', 'Communications relay', 'Japan Ministry of Defense', 'Japan', 'allied'),
    ('DSP', 'Defense Support Program', 'Missile warning', 'U.S. Space Force', 'United States', 'usother'),
    ('STSS', 'Space Tracking and Surveillance System', 'Missile warning', 'Missile Defense Agency', 'United States', 'usother'),
    ('STPSat', 'STPSat-2', 'Technology / undisclosed', 'U.S. Space Force (STP)', 'United States', 'usother'),
    ('PAN', 'PAN (USA 207)', 'SIGINT (eavesdropping)', 'Undisclosed U.S. agency', 'United States', 'usother'),
    ('CLIO', 'CLIO (USA 257)', 'SIGINT (eavesdropping)', 'Undisclosed U.S. agency', 'United States', 'usother'),
    ('Prowler', 'Prowler', 'Space surveillance', 'Undisclosed U.S. agency', 'United States', 'usother'),
    ('OTV', 'X-37B OTV', 'Technology / undisclosed', 'U.S. Space Force', 'United States', 'usother'),
    ('Limasat', 'LIMASat', 'Technology / undisclosed', 'U.S. Space Force', 'United States', 'usother'),
    ('Ekran', 'Ekran', 'Communications relay', 'Russia (Soviet heritage)', 'Russia', 'allied'),
    ('SHIJIAN', 'Shijian 6', 'ELINT (eavesdropping)', 'China PLA', 'China', 'allied'),
    ('ISON', 'Unidentified (ISON tracking)', 'Unknown', 'Unknown', 'Unknown', 'allied'),
    ('Unk', 'Unidentified', 'Unknown', 'Unknown', 'Unknown', 'allied'),
]
def other_meta(name):
    for pre, prog, func, owner, nation, layer in OTHER:
        if name.startswith(pre):
            f = func
            if f is None:
                f = 'Radar imaging' if ('Radar' in name or 'IGS 5A' in name or re.match(r'IGS \d+$', name)) else 'Optical imaging'
                if name in ('IGS 6', 'IGS 7', 'IGS 9'): f = 'Radar imaging'
            return prog, f, owner, nation, layer
    return None

for cospar, (name, l1, l2) in tles.items():
    if cospar in used_tle: continue
    s = sat_by_id.get(cospar)
    kind = 'payload'
    if re.search(r'\b(r|Rk|R/B)$', name) or (s and s['OBJECT_TYPE'] == 'R/B'): kind = 'rocket body'
    elif 'Deb' in name or 'Cover' in name or (s and s['OBJECT_TYPE'] == 'DEB'): kind = 'debris'
    meta = other_meta(name)
    date = s['LAUNCH_DATE'] if s else f"{cospar[:4]}"
    # NRO-associated hardware (rocket bodies / debris from NRO launches)
    nro_hw = name in ('Jumpseat 3 Rk', 'USA 89 r', 'USA 144 Deb', 'USA 225 r', 'Mentor 10 Rk', 'USA 521 r', 'USA 582 r', 'NOSS 2-3 (D)') or (s and s['OBJECT_NAME'].startswith('USA') and kind != 'payload')
    if 'StarSh' in name and kind == 'payload':   # unnumbered or USA-numbered Starshield objects in the element file
        nm = name.replace('StarSh', '').strip()
        o = {'name': (nm + ' (Starshield)') if nm else f'Starshield {cospar}', 'program': 'Starshield', 'function': 'Proliferated architecture', 'kind': kind, 'layer': 'nro',
             'owner': 'NRO (SpaceX-built)', 'nation': 'United States', 'date': date, 'status': 'Active (presumed)', 'cospar': cospar, 'orbit': orbit_class_from_tle(l2),
             'notes': 'Starshield satellite from an NRO proliferated-architecture launch, tracked by amateur observers.', 'links': {}}
    elif nro_hw:
        prog = {'Jumpseat 3 Rk': 'Jumpseat', 'USA 89 r': 'Satellite Data System', 'USA 144 Deb': 'Misty', 'USA 225 r': 'RPP (NROL-66)', 'Mentor 10 Rk': 'Orion 12 (NROL-70)',
                'USA 521 r': 'NROL-174', 'USA 582 r': 'NROL-105 era Vulcan', 'NOSS 2-3 (D)': 'NOSS (Parcae)'}.get(name, 'NRO launch hardware')
        if name == 'NOSS 2-3 (D)': kind = 'payload'
        o = {'name': name, 'program': prog, 'function': 'Launch hardware' if kind != 'payload' else 'Ocean surveillance', 'kind': kind, 'layer': 'nro',
             'owner': 'NRO', 'nation': 'United States', 'date': date, 'status': 'In orbit', 'cospar': cospar,
             'notes': 'Object from an NRO launch, tracked by amateur observers.', 'orbit': orbit_class_from_tle(l2), 'links': {}}
    elif meta:
        prog, func, owner, nation, layer = meta
        o = {'name': name, 'program': prog, 'function': func if kind == 'payload' else 'Launch hardware', 'kind': kind, 'layer': layer,
             'owner': owner, 'nation': nation, 'date': date, 'status': 'In orbit' if nation != 'Unknown' else 'Unidentified object',
             'cospar': cospar, 'orbit': orbit_class_from_tle(l2), 'notes': '', 'links': {}}
    elif s and s['OBJECT_NAME'].startswith('USA'):
        o = {'name': name, 'program': 'Undisclosed U.S. payload', 'function': 'Technology / undisclosed', 'kind': kind, 'layer': 'usother',
             'owner': 'Undisclosed U.S. agency', 'nation': 'United States', 'date': date, 'status': 'In orbit', 'cospar': cospar,
             'orbit': orbit_class_from_tle(l2), 'notes': '', 'links': {}}
    else:
        o = {'name': name, 'program': 'Unidentified', 'function': 'Unknown', 'kind': kind, 'layer': 'allied', 'owner': 'Unknown', 'nation': 'Unknown',
             'date': date, 'status': 'Unidentified object', 'cospar': cospar, 'orbit': orbit_class_from_tle(l2), 'notes': '', 'links': {}}
    if s:
        o['norad'] = int(s['NORAD_CAT_ID']); o['catName'] = s['OBJECT_NAME']
        o['links']['n2yo'] = f"https://www.n2yo.com/satellite/?s={s['NORAD_CAT_ID']}"
        o['links']['heavens'] = f"https://heavens-above.com/satinfo.aspx?satid={s['NORAD_CAT_ID']}"
    o['links']['wiki'] = 'https://en.wikipedia.org/w/index.php?search=' + (o['program'].split(' (')[0]).replace(' ', '+') + '+satellite'
    o.update(tle_fields((name, l1, l2)))
    add(o)

# ---------- post-processing: sites, end dates, representative orbits, models ----------
SITES = {
    'Vandenberg': (34.74, -120.57), 'Cape Canaveral': (28.49, -80.58), 'Kennedy Space Center': (28.61, -80.62),
    'Wallops (MARS)': (37.83, -75.49), 'Mahia (Rocket Lab)': (-39.26, 177.86), 'Tanegashima': (30.40, 130.97),
    'Kourou': (5.24, -52.77), 'Palmachim': (31.88, 34.68), 'Plesetsk': (62.93, 40.57), 'Baikonur': (45.92, 63.34),
    'Jiuquan': (40.96, 100.29), 'Xichang': (28.25, 102.03), 'Taiyuan': (38.85, 111.61), 'Satish Dhawan': (13.72, 80.23),
    'Sea Launch (Pacific)': (0.0, -154.0), 'Yasny': (51.21, 59.85), 'Unknown': None,
}
CODES = {'AFWTR': 'Vandenberg', 'AFETR': 'Cape Canaveral', 'TANSC': 'Tanegashima', 'FRGUI': 'Kourou', 'WLPIS': 'Wallops (MARS)', 'YAVNE': 'Palmachim',
         'RLLB': 'Mahia (Rocket Lab)', 'PLMSC': 'Plesetsk', 'JSC': 'Jiuquan', 'SRILR': 'Satish Dhawan', 'SEAL': 'Sea Launch (Pacific)', 'TYMSC': 'Baikonur',
         'YSLA': 'Yasny', 'XICLF': 'Xichang', 'TAISC': 'Taiyuan'}
def site_name(text, cat):
    t = (text or '')
    if 'url=' in t: t = ''
    tl = t.lower()
    if tl.startswith(('vafb', 'vsfb', 'vandenberg')): return 'Vandenberg'
    if tl.startswith(('ccafs', 'ccsfs', 'cape canaveral', 'cc ')): return 'Cape Canaveral'
    if tl.startswith(('ksc', 'kennedy', 'cck')): return 'Kennedy Space Center'
    if tl.startswith(('mars', 'wallops')): return 'Wallops (MARS)'
    if tl.startswith('mahia'): return 'Mahia (Rocket Lab)'
    if cat and cat.get('LAUNCH_SITE') in CODES: return CODES[cat['LAUNCH_SITE']]
    if tl.startswith('va '): return 'Vandenberg'
    return 'Unknown'

# approximate end-of-life for classified objects whose decay is not in the public catalog
END = {'USA 6': '1994-11-01', 'USA 27': '1996-06-01', 'USA 33': '1996-06-01', 'USA 86': '2000-06-01', 'USA 116': '2008-11-01',
       'USA 129': '2014-05-01', 'USA 161': '2014-11-01', 'USA 34': '1997-03-25', 'USA 69': '2011-03-26', 'USA 133': '2015-05-01',
       'USA 152': '2014-07-01', 'USA 182': '2016-06-01', 'USA 193': '2008-02-21', 'OPS 5705': '1979-01-28', 'OPS 4515': '1981-08-23',
       'OPS 2581': '1982-10-30', 'OPS 3984': '1984-11-23', 'OPS 9627': '1985-08-13'}

# representative orbit defaults by program keyword: (perigee km, apogee km, inclination deg)
REP = [('kh-11', (265, 1000, 97.9)), ('misty', (700, 800, 65)), ('lacrosse', (680, 690, 57)), ('topaz', (1085, 1110, 123)),
       ('intruder', (1000, 1200, 63.4)), ('noss', (1050, 1180, 63.4)), ('quasar', (1000, 39000, 63.4)), ('satellite data', (1000, 39000, 63.4)),
       ('orion', (35600, 35950, 6)), ('mentor', (35600, 35950, 6)), ('magnum', (35700, 35900, 5)), ('trumpet', (1300, 39000, 63.4)),
       ('jumpseat', (1200, 39000, 63.4)), ('mercury', (35700, 35900, 7)), ('canyon', (30000, 40000, 10)), ('rhyolite', (35700, 35900, 3)),
       ('chalet', (35600, 36000, 8)), ('vortex', (35600, 36000, 8)), ('sharp', (35770, 35810, 1.4)), ('silentbarker', (35770, 35810, 0.1)),
       ('starshield', (310, 425, 69.7)), ('stex', (600, 750, 85)), ('geolite', (35700, 35900, 1)), ('rpp', (1214, 1232, 90.1)),
       ('corona', (180, 400, 80)), ('argon', (300, 400, 82)), ('lanyard', (170, 280, 75)), ('gambit', (130, 300, 95)), ('hexagon', (160, 270, 96.5)),
       ('grab', (600, 1000, 67)), ('poppy', (900, 1000, 70))]
def rep_orbit(o):
    m = re.search(r'([\d,]+)\s*[×x]\s*([\d,]+)\s*km\s*[×x]\s*([\d.]+)', o.get('orbitText') or '')
    if m:
        a, p, i = (float(x.replace(',', '')) for x in m.groups())
        return [min(a, p), max(a, p), i]
    pl = (o.get('program') or '').lower()
    for k, v in REP:
        if k in pl: return list(v)
    cls = o.get('orbit')
    if cls == 'GEO': return [35700, 35900, 5]
    if cls == 'HEO / Molniya': return [1000, 39000, 63.4]
    if cls == 'MEO': return [11081, 11105, 58.5]
    inc = 70 if 'Electron' in (o.get('rocket') or '') or 'Minotaur' in (o.get('rocket') or '') else 97
    return [500, 600, inc]

def model_for(o):
    f = o['function']; p = (o.get('program') or '').lower(); k = o['kind']
    if k == 'rocket body': return 'rocket'
    if k == 'debris': return 'debris'
    if k == 'program' or 'corona' in p or 'gambit' in p or 'hexagon' in p: return 'film' if f == 'Optical imaging' else 'elint-early'
    if f == 'Optical imaging': return 'optical'
    if f == 'Radar imaging': return 'radar'
    if f == 'Ocean surveillance': return 'noss'
    if f == 'SIGINT (eavesdropping)': return 'sigint-geo'
    if f == 'ELINT (eavesdropping)': return 'elint-heo' if o.get('orbit') == 'HEO / Molniya' else 'sigint-geo'
    if f == 'Communications relay': return 'relay'
    if f == 'Proliferated architecture': return 'starshield'
    if f == 'Space surveillance': return 'ssa'
    if f == 'Navigation': return 'relay'
    if f == 'Missile warning': return 'sigint-geo'
    if f == 'Unknown': return 'unknown'
    return 'tech'

for i, o in enumerate(objects):
    o['id'] = i
    if o.get('nrol') == 'NROL-113':
        o.update(program='Starshield', function='Proliferated architecture', status='Active (presumed)', rocket='Falcon 9 Block 5',
                 site='VSFB, SLC-4E', orbitText='LEO', orbit='LEO', owner='NRO (SpaceX-built)', notes="NRO's Proliferated Architecture Mission of 21 Starshield satellites.")
    cat = sat_by_id.get(o.get('cospar')) if o.get('cospar') else None
    o['siteName'] = site_name(o.get('site'), cat)
    o['year'] = int(o['date'][:4]) if o.get('date') else None
    if o.get('date') and len(o['date']) == 4: o['date'] = o['date'] + '-01-01'; o['dateApprox'] = True
    end = o.get('decayed') or END.get(o.get('usa') or '') or END.get(o.get('catName') or '') or o.get('endDate')
    if end:
        o['end'] = end
        if o['status'] not in ('Launch failure', 'Program ended, all decayed'): o['status'] = 'Decayed'
    if o['status'] == 'Launch failure': o['end'] = o['date']
    if o['status'] == 'Decayed' and not o.get('end'): o['end'] = str(o['year'] + 3) + '-01-01'; o['endApprox'] = True
    if not o.get('tle'):
        o['rep'] = rep_orbit(o)
    o['model'] = model_for(o)
    fam = o.get('program') or 'Undisclosed'
    fam = re.sub(r'\s*\(.*\)\s*$', '', fam) if not fam.startswith(('CORONA','GAMBIT','ARGON','LANYARD','HEXAGON')) else fam.split(' (')[0]
    fam = re.sub(r'\s+F/O\s*\d*$', '', fam)
    fam = re.sub(r'\s*\d+[A-Z]?(\s*&\s*\d*[A-Z]?)?\s*$', '', fam)
    fam = {'Improved Trumpet': 'Trumpet', 'SIGINT High Altitude Replenishment Program': 'SHARP', 'Satellite Data System': 'Quasar / SDS', 'Quasar': 'Quasar / SDS', 'SDS': 'Quasar / SDS',
           'Mentor': 'Orion', 'Orion': 'Orion', 'Magnum / Orion': 'Orion', 'Orion (Mentor)': 'Orion', 'Intruder': 'NOSS / Intruder', 'NOSS': 'NOSS / Intruder', 'NOSS (Parcae)': 'NOSS / Intruder',
           'Lacrosse': 'Lacrosse / Onyx', 'Topaz': 'Topaz (FIA Radar)', 'KH-11 Kennen': 'KH-11', 'Chalet / Vortex': 'Chalet / Vortex', 'Rhyolite / Aquacade': 'Rhyolite / Aquacade', 'LEO': 'Starshield'}.get(fam, fam)
    o['family'] = (fam or 'Undisclosed').rstrip('- ').strip() or 'Undisclosed'
    o['tracked'] = 'Public elements (amateur-tracked)' if o.get('tle') else ('Program (no orbit data)' if o['kind'] == 'program' else 'No public elements (representative orbit)')
    for k in ('site', 'orbitText', 'catName', 'patch', 'tleName'):
        if k in o and not o[k]: del o[k]
    if 'url=' in (o.get('site') or ''): o['site'] = 'VSFB, SLC-4E'
    o['decade'] = decade_of(o.get('date')) if o['kind'] != 'program' else o['decade']
    o['decades'] = [o['decade']] if o['kind'] != 'program' else o['decades']
meta_sites = {k: v for k, v in SITES.items() if v}

land = json.load(open(d + '/land.json'))
epochs = [o['epoch'] for o in objects if o.get('epoch')]
meta = {'built': datetime.date.today().isoformat(), 'tleCount': len(epochs), 'tleNewest': max(epochs), 'tleOldest': min(epochs),
        'tleSource': 'Mike McCants classfd.tle (amateur observations)', 'catalog': 'CelesTrak SATCAT', 'launches': 'Wikipedia: List of NRO launches; Gunter\'s Space Page'}
borders = json.load(open(d + '/borders.json')) if os.path.exists(d + '/borders.json') else []
cities = json.load(open(d + '/cities.json', encoding='utf-8')) if os.path.exists(d + '/cities.json') else []
def opt(name):
    f = d + '/' + name
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else None
json.dump({'objects': objects, 'land': land, 'borders': borders, 'cities': cities, 'meta': meta, 'content': opt('content.json'), 'images': opt('images.json') or [], 'social': opt('social.json') or [], 'weather': opt('weather.json') or {}, 'news': opt('news.json') or {'items': [], 'major': []}, 'geoid': opt('geoid.json'), 'launches': opt('launches.json') or {'previous': [], 'upcoming': [], 'asof': ''}}, open(d + '/data.json', 'w'), separators=(',', ':'))

c = collections.Counter
print('objects', len(objects), 'with tle', len(epochs))
print('layer', c(o['layer'] for o in objects))
print('kind', c(o['kind'] for o in objects))
print('function', c(o['function'] for o in objects))
print('orbit', c(o['orbit'] for o in objects))
print('status', c(o['status'] for o in objects))
print('decade', sorted(c(o['decade'] for o in objects).items(), key=lambda x: str(x[0])))
print('nation', c(o['nation'] for o in objects))
print('owner', c(o['owner'] for o in objects))
print('nro with tle', sum(1 for o in objects if o['layer'] == 'nro' and o.get('tle')))
for o in objects:
    if o['layer'] == 'nro' and o['kind'] == 'payload' and not o.get('tle') and o['status'] in ('Active (presumed)', 'In orbit, status unknown'):
        print('  no tle:', o['name'], o.get('nrol'), o['program'], o['status'])
import os; print('size', os.path.getsize(d + '/data.json'))
