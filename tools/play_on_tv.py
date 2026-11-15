# ----------------------------------------------------------------------------------------------------------------------
# Roster-5 Satellite Live Viewer
# play_on_tv.py - sends a video file to a DLNA television on the local network and tells it to play
#
# Author:        Chad Burge
# Created:       2026-11-15
# Repository:    github.com/chadburge/nro-orbit-watch (private) - working copy C:\Users\chadd\dev\nro-orbit-watch
# Project:       a live and historical 3D/2D viewer of U.S. reconnaissance satellites built from public data, with a
#                wall-display "lobby" show customised for Roster-5 Software (Louisville, Colorado)
# Ownership:     Copyright (c) 2026 Chad Burge. All rights reserved. This code and its data pipeline are my own work;
#                any use, copying or redistribution requires my written permission (see LICENSE).
# ----------------------------------------------------------------------------------------------------------------------
"""Play a local video on a DLNA/UPnP television (a Hisense Android TV, for one) without any app on the TV.

    python tools/play_on_tv.py "C:\\Users\\chadd\\Videos\\Roster-5 Satellite Live Viewer - lobby show 4K60.mp4"
    python tools/play_on_tv.py --find                 list the renderers that answer on the network
    python tools/play_on_tv.py --stop                 stop playback on the first renderer found

The script serves the file from this PC over HTTP (the TV pulls it), then sends the UPnP AVTransport calls
SetAVTransportURI and Play. Keep it running while the TV plays; Ctrl+C stops serving. Windows may ask once to allow
Python through the firewall for the private network; that is what lets the TV reach the file.
"""
import argparse, os, re, socket, sys, threading, time, urllib.request, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

def discover(timeout=3.0):
    msg = ('M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 2\r\n'
           'ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n\r\n').encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP); s.settimeout(timeout)
    for _ in range(2): s.sendto(msg, ('239.255.255.250', 1900))
    found = {}; t0 = time.time()
    while time.time() - t0 < timeout:
        try: data, addr = s.recvfrom(4096)
        except socket.timeout: break
        m = re.search(r'(?i)location:\s*(\S+)', data.decode(errors='ignore'))
        if m: found[addr[0]] = m.group(1)
    out = []
    for ip, loc in found.items():
        try:
            x = urllib.request.urlopen(loc, timeout=4).read().decode(errors='ignore')
            name = re.search(r'<friendlyName>(.*?)</friendlyName>', x); ctl = re.search(r'<serviceType>urn:schemas-upnp-org:service:AVTransport:1</serviceType>.*?<controlURL>(.*?)</controlURL>', x, re.S)
            if ctl: out.append({'ip': ip, 'name': name.group(1) if name else ip, 'control': urllib.parse.urljoin(loc, ctl.group(1))})
        except Exception as e: print('  (could not read', loc, e, ')')
    return out

def soap(control, action, body):
    env = ('<?xml version="1.0"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
           '<u:%s xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID>%s</u:%s></s:Body></s:Envelope>') % (action, body, action)
    req = urllib.request.Request(control, env.encode('utf-8'), {'Content-Type': 'text/xml; charset="utf-8"', 'SOAPAction': '"urn:schemas-upnp-org:service:AVTransport:1#%s"' % action})
    with urllib.request.urlopen(req, timeout=10) as r: return r.read().decode(errors='ignore')

def my_ip(peer):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect((peer, 80)); ip = s.getsockname()[0]; s.close(); return ip

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('file', nargs='?'); ap.add_argument('--find', action='store_true'); ap.add_argument('--stop', action='store_true'); ap.add_argument('--tv', help='renderer name or IP to use'); ap.add_argument('--port', type=int, default=8790)
    a = ap.parse_args()
    tvs = discover()
    if a.find or not tvs:
        print('renderers found:' if tvs else 'no DLNA renderer answered (is the TV on and on the same network?)')
        for t in tvs: print('  ', t['name'], t['ip'])
        if a.find or not tvs: return
    tv = next((t for t in tvs if a.tv and (a.tv.lower() in t['name'].lower() or a.tv == t['ip'])), tvs[0])
    if a.stop: soap(tv['control'], 'Stop', ''); print('stopped', tv['name']); return
    if not a.file or not os.path.exists(a.file): print('give the path of a video file'); return
    folder, name = os.path.split(os.path.abspath(a.file)); ip = my_ip(tv['ip'])
    class H(SimpleHTTPRequestHandler):
        def __init__(self, *x, **k): super().__init__(*x, directory=folder, **k)
        def log_message(self, *x): pass
    srv = ThreadingHTTPServer(('0.0.0.0', a.port), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = 'http://%s:%d/%s' % (ip, a.port, urllib.parse.quote(name))
    meta = ('&lt;DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"&gt;'
            '&lt;item id="0" parentID="-1" restricted="1"&gt;&lt;dc:title&gt;%s&lt;/dc:title&gt;&lt;upnp:class&gt;object.item.videoItem&lt;/upnp:class&gt;'
            '&lt;res protocolInfo="http-get:*:video/mp4:*"&gt;%s&lt;/res&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;') % (name.replace('&', '&amp;'), url)
    soap(tv['control'], 'SetAVTransportURI', '<CurrentURI>%s</CurrentURI><CurrentURIMetaData>%s</CurrentURIMetaData>' % (url, meta))
    soap(tv['control'], 'Play', '<Speed>1</Speed>')
    print('playing on', tv['name'], 'from', url, '- Ctrl+C here when done')
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        try: soap(tv['control'], 'Stop', '')
        except Exception: pass
        srv.shutdown()

main()
