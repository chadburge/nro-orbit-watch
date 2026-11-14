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
    cells = [clean(c) for c in cells]
    if len(cells) < 10 or not cells[0].startswith('NROL'):
        continue
    keys = ['nrol', 'nick', 'usa', 'date', 'site', 'rocket', 'orbit', 'project', 'function', 'status', 'patch', 'remarks']
    rows.append(dict(zip(keys, cells + [''] * (12 - len(cells)))))
print(len(rows))
for r in rows[:2] + rows[-3:]:
    print(r)
json.dump(rows, open(d + '/nrol.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print(collections.Counter(r['status'] for r in rows).most_common())
print(sorted(set(re.sub(r'\s*\d+\s*$', '', r['project']) for r in rows)))
print(sorted(set(r['function'] for r in rows)))
