# ----------------------------------------------------------------------------------------------------------------------
# Roster-5 Satellite Live Viewer
# capture_lobby.py - records the lobby show, frame by frame, into a 4K 60 fps video for sharing
#
# Author:        Chad Burge
# Created:       2026-11-15
# Repository:    github.com/chadburge/nro-orbit-watch (private) - working copy C:\Users\chadd\dev\nro-orbit-watch
# Project:       a live and historical 3D/2D viewer of U.S. reconnaissance satellites built from public data, with a
#                wall-display "lobby" show customised for Roster-5 Software (Louisville, Colorado)
# Ownership:     Copyright (c) 2026 Chad Burge. All rights reserved. This code and its data pipeline are my own work;
#                any use, copying or redistribution requires my written permission (see LICENSE).
# ----------------------------------------------------------------------------------------------------------------------
"""Record the lobby show to an MP4 without a screen.

The page is driven by a headless Chromium under "begin frame control": the browser renders exactly one frame each time it
is asked, with the page's clocks advanced by 1/60 s, and hands the frame back as a JPEG. That makes the capture frame
exact at any resolution regardless of how fast the machine can actually draw it: a 4K frame takes ~100 ms to render and
encode, so two hours of show take about twelve hours of wall-clock time. CSS transitions and SVG animations run on the
document's wall clock rather than the virtual one, so a small driver pauses them and advances them per frame too.

    python tools/capture_lobby.py                          two hours (or until the show has played everything) at 3840x2160, 60 fps
    python tools/capture_lobby.py --hours 0.05             a three-minute test
    python tools/capture_lobby.py --intro-frames DIR       JPEG frames (0000.jpg ...) to play before the show, e.g. the logo reveal

Output goes to %USERPROFILE%\\Videos by default as HEVC (H.265) in an MP4, encoded on the GPU. Requires ffmpeg with
hevc_nvenc and the Python playwright package with its bundled Chromium.
"""
import argparse, asyncio, base64, datetime, glob, os, socket, subprocess, sys, threading, time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
FLAGS = ['--enable-begin-frame-control', '--run-all-compositor-stages-before-draw', '--disable-new-content-rendering-timeout',
         '--disable-threaded-animation', '--disable-threaded-scrolling', '--disable-checker-imaging', '--disable-image-animation-resync',
         '--use-gl=angle', '--use-angle=d3d11', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required', '--mute-audio']
DRIVER = """() => {
  window.__capStep = (dt) => {
    for (const a of document.getAnimations()) { try { if (a.playState === 'running' || a.playState === 'pending') a.pause(); if (a.playState === 'paused') a.currentTime = (a.currentTime || 0) + dt; } catch (e) {} }
    for (const sv of document.querySelectorAll('svg')) { try { if (!sv.animationsPaused()) sv.pauseAnimations(); sv.setCurrentTime(sv.getCurrentTime() + dt / 1000); } catch (e) {} }
    for (const v of document.querySelectorAll('video')) { try { if (!v.paused) v.pause(); } catch (e) {} }
  };
  return true;
}"""

class Quiet(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=SITE, **k)
    def log_message(self, *a): pass

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(os.path.expanduser('~'), 'Videos', 'Roster-5 Satellite Live Viewer - lobby show 4K60.mp4'))
    ap.add_argument('--hours', type=float, default=2.0)
    ap.add_argument('--width', type=int, default=3840); ap.add_argument('--height', type=int, default=2160); ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--intro-frames', default=None, help='folder of JPEG frames to play first')
    ap.add_argument('--quality', type=int, default=92, help='JPEG quality of captured frames')
    ap.add_argument('--cq', type=int, default=23, help='HEVC constant quality (lower = better, bigger)')
    ap.add_argument('--settle', type=float, default=12, help='seconds of real time to let the page load before recording')
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    log = open(a.out + '.log', 'a', encoding='utf-8')
    def say(*m):
        line = f'{datetime.datetime.now():%H:%M:%S} ' + ' '.join(str(x) for x in m); print(line, flush=True); log.write(line + '\n'); log.flush()

    port = free_port(); srv = ThreadingHTTPServer(('127.0.0.1', port), Quiet); threading.Thread(target=srv.serve_forever, daemon=True).start()
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(a.fps), '-c:v', 'mjpeg', '-i', '-',
                           '-c:v', 'hevc_nvenc', '-preset', 'p5', '-tune', 'hq', '-rc', 'vbr', '-cq', str(a.cq), '-b:v', '0', '-maxrate', '60M', '-bufsize', '120M',
                           '-pix_fmt', 'yuv420p', '-tag:v', 'hvc1', '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
    frames = 0
    if a.intro_frames:
        files = sorted(glob.glob(os.path.join(a.intro_frames, '*.jpg')))
        for f in files: ff.stdin.write(open(f, 'rb').read()); frames += 1
        say('intro frames', len(files))

    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=FLAGS)
        pg = await b.new_page(viewport={'width': a.width, 'height': a.height}, device_scale_factor=1)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(f'http://127.0.0.1:{port}/index.html#lobby,capture'); await asyncio.sleep(a.settle)
        await pg.evaluate(DRIVER)
        cdp = await pg.context.new_cdp_session(pg)
        await cdp.send('Emulation.setVirtualTimePolicy', {'policy': 'pause'})
        tick = 1000 / a.fps; total = int(a.hours * 3600 * a.fps); t0 = time.time(); last = t0; shown = 0
        say('recording', a.width, 'x', a.height, a.fps, 'fps, up to', total, 'frames ->', a.out)
        n = 0
        while n < total:
            fut = asyncio.get_event_loop().create_future()
            cdp.once('Emulation.virtualTimeBudgetExpired', lambda _: fut.done() or fut.set_result(1))
            await cdp.send('Emulation.setVirtualTimePolicy', {'policy': 'advance', 'budget': tick})
            try: await asyncio.wait_for(fut, 30)
            except asyncio.TimeoutError: say('virtual time stalled at frame', n)
            await pg.evaluate('dt => window.__capStep(dt)', tick)
            r = await cdp.send('HeadlessExperimental.beginFrame', {'interval': tick, 'screenshot': {'format': 'jpeg', 'quality': a.quality}})
            data = r.get('screenshotData')
            if data: last_jpg = base64.b64decode(data)
            ff.stdin.write(last_jpg); n += 1; frames += 1
            if n % 600 == 0:
                st = await pg.evaluate('() => window.__lobbyStats ? window.__lobbyStats() : null')
                now = time.time(); say(f'frame {n}/{total}  video {n / a.fps / 60:.1f} min  wall {(now - t0) / 60:.1f} min  {600 / (now - last):.1f} fps  slides {st}'); last = now
                if errs: say('page errors:', errs[:3]); errs.clear()
                # stop early once the show has run out of new slides (nothing new in the last 15 slides, after an hour at least)
                if st and n > 3600 * a.fps and st['sinceNew'] >= 15: say('every slide has played; stopping'); break
        await b.close()
    ff.stdin.close(); ff.wait(); srv.shutdown()
    say('done:', frames, 'frames,', f'{frames / a.fps / 60:.1f} min,', os.path.getsize(a.out) / 1e9, 'GB')

asyncio.run(main())
