# ----------------------------------------------------------------------------------------------------------------------
# Roster-5 Satellite Live Viewer
# parse_nrol.py - parses the Wikipedia "List of NRO launches" wikitext into structured mission rows
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
import json, re, sys, collections
import os
d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
t = json.load(open(d + '/nro_wikitext.json', encoding='utf-8'))['parse']['wikitext']
sec = t[t.index('== Launch history =='):t.index('==Gallery==')]

def clean(s):
    s = re.sub(r'<ref[^>]*/>', '', s)
    s = re.sub(r'<ref[^>]*>.*?</ref>', '', s, flags=re.S)
    s = re.sub(r'\{\{nts\|(\d+)\}\}', r'\1', s)
    s = re.sub(r'\{\{dts\|([^}]*)\}\}', r'\1', s)
    s = re.sub(r'\{\{nowrap\|([^}]*)\}\}', r'\1', s)
    s = re.sub(r'\{\{[^}]*\}\}', '', s)
    s = re.sub(r'\[\[File:[^\]]*\]\]', '', s)
    s = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', s)
    s = re.sub(r'\[https?://\S+ ([^\]]*)\]', r'\1', s)
    s = re.sub(r"'''?", '', s)
    s = s.replace('<br />', ' ').replace('<br/>', ' ').replace('<br>', ' ').replace('&nbsp;', ' ')
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'^style="[^"]*"\s*\|\s*', '', s.strip())
    return re.sub(r'\s+', ' ', s).strip()

rows = []
for block in re.split(r'\n\|-[^\n]*\n', sec)[1:]:
    cells = re.split(r'\n\|', "\n" + block.strip('\n'))[1:]
    raw = cells[:]
    cells = [clean(c) for c in cells]
    if len(cells) < 10 or not cells[0].startswith('NROL'):
        continue
    patch = None
    for c in raw:
        m = re.search(r'\[\[File:([^\]|]+)', c)
        if m and 'atch' in m.group(1):
            patch = m.group(1).strip()
    keys = ['nrol', 'nick', 'usa', 'date', 'site', 'rocket', 'orbit', 'project', 'function', 'status', 'patch', 'remarks']
    row = dict(zip(keys, cells + [''] * (12 - len(cells))))
    row['patchFile'] = patch
    rows.append(row)
print(len(rows))
for r in rows[:2] + rows[-3:]:
    print(r)
json.dump(rows, open(d + '/nrol.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print(collections.Counter(r['status'] for r in rows).most_common())
print(sorted(set(re.sub(r'\s*\d+\s*$', '', r['project']) for r in rows)))
print(sorted(set(r['function'] for r in rows)))
