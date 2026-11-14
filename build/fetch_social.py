"""Company social posts for the lobby show -> data/social.json.

LinkedIn, X and Facebook all sit behind log-in walls for automated clients, so this script does not scrape them.
Instead it merges two inputs and screens every item before the page can show it:

  data/social_raw.json   posts pasted by hand (or exported from LinkedIn's "Download your data"), a list of objects with
                         id, source, date, title, text, link, image (optional key in images.json)
  data/social.json       the curated output; items keep an "approved" flag the show requires

Screening removes anything a company would not want on its lobby wall: profanity, politics, money and personnel matters,
anything that reads as internal or sensitive, posts longer than 700 characters, and posts with no text. A rejected post is
written with approved=false and a "why" field so it can be reviewed, never shown. Run after editing social_raw.json:

  python build/fetch_social.py
"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
RAW = os.path.join(DATA, 'social_raw.json'); OUT = os.path.join(DATA, 'social.json')

BLOCK = re.compile(r"\b(fuck|shit|damn|crap|hell|ass|salary|salaries|pay ?rate|layoff|laid off|lawsuit|sued|fired|resign\w*|politic\w*|election|trump|biden|democrat\w*|republican\w*|classified|secret|password|confidential|proprietary|internal only|do not share|divorce|arrest\w*|dui|drunk|hangover|strip|sex\w*|funeral|died|death|covid|vaccin\w*|protest\w*|war|israel|gaza|ukraine|russia|china|revenue|profit|margin|funding|acqui\w*|merger|customer name|contract value|\$\s?\d)\b", re.I)
PII = re.compile(r"(\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}|[\w.+-]+@[\w-]+\.[\w.]+|\b\d{1,5} [A-Z][a-z]+ (?:St|Ave|Blvd|Dr|Rd)\b)")

def screen(p):
    txt = (p.get('title') or '') + ' ' + (p.get('text') or '')
    if not (p.get('text') or '').strip(): return 'no text'
    if len(txt) > 700: return 'too long for a lobby slide'
    m = BLOCK.search(txt)
    if m: return 'contains "%s"' % m.group(0)
    m = PII.search(txt)
    if m: return 'contains contact details or an address (%s)' % m.group(0)
    return None

def load(path):
    try: return json.load(open(path, encoding='utf-8'))
    except FileNotFoundError: return []

cur = {p['id']: p for p in load(OUT)}
for p in load(RAW):
    if not p.get('id'): continue
    why = screen(p)
    q = dict(p); q['approved'] = why is None
    if why: q['why'] = why
    elif 'why' in q: del q['why']
    cur[p['id']] = q
for p in cur.values():            # re-screen curated items too, in case the rules tightened
    why = screen(p)
    if why: p['approved'] = False; p['why'] = why
json.dump(list(cur.values()), open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
ok = [p for p in cur.values() if p.get('approved')]
print('%d posts, %d approved' % (len(cur), len(ok)))
for p in cur.values():
    if not p.get('approved'): print('  rejected', p['id'], '-', p.get('why'))
