# ----------------------------------------------------------------------------------------------------------------------
# Roster-5 Satellite Live Viewer
# run.py - local server, nightly data refresh and the command-line entry point for the whole pipeline
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
"""Serve the site locally and keep its data fresh.

    python run.py                 serve site/ on http://localhost:8787 (refreshes first if the data is older than a day)
    python run.py --build         rebuild site/index.html from data/data.json first
    python run.py --refresh       download everything (including the slow image passes), rebuild, then serve
    python run.py --refresh-data  daily data refresh only (elements, catalog, launches, weather, headlines, posts), then exit

While serving, a background thread repeats the daily refresh every night at 03:30 local time; the page notices the new build
and reloads itself between lobby segments. A Windows scheduled task can also run --refresh-data so the data stays current
even when the server is not running.
"""
import datetime, json, os, runpy, subprocess, sys, threading, time, traceback, webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import PIL.Image   # imported here so the packaged executable carries the imaging library the refresh steps need

# Packaged as a Windows executable (PyInstaller), the site, data and build folders travel inside the app folder and the
# build steps run inside the executable itself (see --step below) because there is no separate Python interpreter.
FROZEN = getattr(sys, 'frozen', False)
ROOT = getattr(sys, '_MEIPASS', None) if FROZEN else os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, 'site')
DATA = os.path.join(ROOT, 'data')
PORT = int(os.environ.get('PORT', '8787'))
REFRESH_HOUR, REFRESH_MINUTE = 3, 30
USAGE_URL = ''   # usage relay (tools/usage-worker): when set, each start of the server sends a one-line ping; empty = off

def usage_ping():
    if not USAGE_URL: return
    try:
        import urllib.request, platform
        body = json.dumps({'mode': 'server', 'host': 'app' if FROZEN else 'run.py', 'build': json.load(open(os.path.join(SITE, 'build.json'))).get('built', '') if os.path.exists(os.path.join(SITE, 'build.json')) else '', 'id': 'srv', 'screen': '', 'ua': platform.platform()}).encode()
        urllib.request.urlopen(urllib.request.Request(USAGE_URL, body, {'Content-Type': 'text/plain'}), timeout=10).read()
    except Exception: pass
LOG = os.path.join(DATA, 'refresh.log')

def run(script, *args):
    if FROZEN: subprocess.run([sys.executable, '--step', script, *args], check=True, cwd=ROOT)
    else: subprocess.run([sys.executable, os.path.join(ROOT, 'build', script), *args], check=True, cwd=ROOT)

if len(sys.argv) > 2 and sys.argv[1] == '--step':   # run one build script in this process (packaged mode)
    path = os.path.join(ROOT, 'build', sys.argv[2]); sys.argv = [path] + sys.argv[3:]; os.chdir(ROOT); runpy.run_path(path, run_name='__main__'); sys.exit(0)

DAILY = ['fetch_inputs.py', 'fetch_launches.py', 'parse_nrol.py', 'fetch_social.py', 'fetch_weather.py', 'fetch_news.py', 'content.py', 'build_data.py', 'build_page.py']
FULL = ['fetch_inputs.py', 'fetch_launches.py', 'fetch_images.py', 'parse_nrol.py', ('fetch_mission_images.py', 'all'), 'fetch_social.py', 'fetch_weather.py', 'fetch_news.py', 'geoid.py', 'land.py', 'borders.py', 'content.py', 'build_data.py', 'build_page.py']

def refresh(steps, label):
    """Run a chain of build steps; a failing download step is logged and skipped so the rebuild still happens."""
    started = datetime.datetime.now()
    with open(LOG, 'a', encoding='utf-8') as log:
        log.write(f'\n== {label} refresh started {started:%Y-%m-%d %H:%M}\n')
        for step in steps:
            name, args = (step, ()) if isinstance(step, str) else (step[0], step[1:])
            try:
                run(name, *args); log.write(f'  ok   {name} {" ".join(args)}\n')
            except Exception as e:
                log.write(f'  FAIL {name}: {e}\n')
                if name in ('build_data.py', 'build_page.py'): raise
        log.write(f'== finished {datetime.datetime.now():%Y-%m-%d %H:%M} ({(datetime.datetime.now() - started).seconds} s)\n')
    json.dump({'built': datetime.datetime.now().isoformat(timespec='seconds')}, open(os.path.join(SITE, 'build.json'), 'w'))

def data_age_hours():
    try: return (time.time() - os.path.getmtime(os.path.join(DATA, 'data.json'))) / 3600
    except OSError: return 1e9

def daily_loop():
    while True:
        now = datetime.datetime.now()
        nxt = now.replace(hour=REFRESH_HOUR, minute=REFRESH_MINUTE, second=0, microsecond=0)
        if nxt <= now: nxt += datetime.timedelta(days=1)
        time.sleep(max(60, (nxt - now).total_seconds()))
        try: refresh(DAILY, 'nightly')
        except Exception: traceback.print_exc()

if '--refresh-data' in sys.argv:
    refresh(DAILY, 'scheduled'); sys.exit(0)
if '--refresh' in sys.argv:
    refresh(FULL, 'full')
elif '--build' in sys.argv or not os.path.exists(os.path.join(SITE, 'index.html')):
    run('build_page.py')
elif data_age_hours() > 20:
    try: refresh(DAILY, 'startup')
    except Exception: traceback.print_exc()
if not os.path.exists(os.path.join(SITE, 'build.json')):
    json.dump({'built': datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(SITE, 'index.html'))).isoformat(timespec='seconds')}, open(os.path.join(SITE, 'build.json'), 'w'))

class Quiet(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=SITE, **k)
    def end_headers(self):
        if self.path.endswith('build.json'): self.send_header('Cache-Control', 'no-store')
        super().end_headers()
    def log_message(self, *a):
        pass

server = ThreadingHTTPServer(('127.0.0.1', PORT), Quiet)
url = f'http://localhost:{PORT}/'
print(f'Roster-5 Satellite Live Viewer at {url}  (nightly data refresh at {REFRESH_HOUR:02d}:{REFRESH_MINUTE:02d}; Ctrl+C to stop)')
threading.Thread(target=daily_loop, daemon=True).start(); threading.Thread(target=usage_ping, daemon=True).start()
threading.Timer(0.6, lambda: webbrowser.open(url)).start()
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
