"""Serve the site locally and open it in the default browser.

    python run.py            serve site/ on http://localhost:8787
    python run.py --build    rebuild site/index.html from data/data.json first
    python run.py --refresh  download new orbital elements and catalog, rebuild everything, then serve
"""
import os, subprocess, sys, threading, webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, 'site')
PORT = int(os.environ.get('PORT', '8787'))

def run(script):
    subprocess.run([sys.executable, os.path.join(ROOT, 'build', script)], check=True, cwd=ROOT)

if '--refresh' in sys.argv:
    run('fetch_inputs.py'); run('parse_nrol.py'); run('land.py'); run('borders.py'); run('build_data.py'); run('build_page.py')
elif '--build' in sys.argv or not os.path.exists(os.path.join(SITE, 'index.html')):
    run('build_page.py')

class Quiet(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=SITE, **k)
    def log_message(self, *a):
        pass

server = ThreadingHTTPServer(('127.0.0.1', PORT), Quiet)
url = f'http://localhost:{PORT}/'
print(f'NRO Orbit Watch running at {url}  (Ctrl+C to stop)')
threading.Timer(0.6, lambda: webbrowser.open(url)).start()
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
