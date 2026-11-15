# ----------------------------------------------------------------------------------------------------------------------
# Roster-5 Satellite Live Viewer
# borders.py - country borders and major cities for the reference layers
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
"""Extract country boundary arcs (borders plus coastlines) from world-atlas countries-110m.json into data/borders.json,
and write the major-cities reference list into data/cities.json."""
import json, os, sys
d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
t = json.load(open(os.path.join(d, 'countries110.json'), encoding='utf-8'))
sc, tr = t['transform']['scale'], t['transform']['translate']
arcs = []
for arc in t['arcs']:
    x = y = 0; pts = []
    for dx, dy in arc:
        x += dx; y += dy
        pts.extend((round(x * sc[0] + tr[0], 2), round(y * sc[1] + tr[1], 2)))
    if len(pts) >= 4:
        arcs.append(pts)
json.dump(arcs, open(os.path.join(d, 'borders.json'), 'w'), separators=(',', ':'))

CITIES = [  # name, lat, lon  (major cities and capitals for orientation)
    ('Washington', 38.90, -77.04), ('New York', 40.71, -74.01), ('Los Angeles', 34.05, -118.24), ('Chicago', 41.88, -87.63), ('Houston', 29.76, -95.37), ('Denver', 39.74, -104.99), ('Seattle', 47.61, -122.33), ('Miami', 25.76, -80.19),
    ('Anchorage', 61.22, -149.90), ('Honolulu', 21.31, -157.86), ('Mexico City', 19.43, -99.13), ('Havana', 23.11, -82.37), ('Panama City', 8.98, -79.52), ('Bogotá', 4.71, -74.07), ('Lima', -12.05, -77.04), ('Santiago', -33.45, -70.67),
    ('Buenos Aires', -34.60, -58.38), ('São Paulo', -23.55, -46.63), ('Rio de Janeiro', -22.91, -43.17), ('Brasília', -15.79, -47.88), ('Caracas', 10.48, -66.90), ('Toronto', 43.65, -79.38), ('Vancouver', 49.28, -123.12), ('Ottawa', 45.42, -75.70),
    ('London', 51.51, -0.13), ('Paris', 48.86, 2.35), ('Berlin', 52.52, 13.41), ('Madrid', 40.42, -3.70), ('Rome', 41.90, 12.50), ('Moscow', 55.76, 37.62), ('Kyiv', 50.45, 30.52), ('Warsaw', 52.23, 21.01), ('Stockholm', 59.33, 18.07),
    ('Istanbul', 41.01, 28.98), ('Ankara', 39.93, 32.86), ('Athens', 37.98, 23.73), ('Reykjavik', 64.15, -21.94), ('Cairo', 30.04, 31.24), ('Lagos', 6.52, 3.38), ('Nairobi', -1.29, 36.82), ('Johannesburg', -26.20, 28.05), ('Cape Town', -33.92, 18.42),
    ('Kinshasa', -4.44, 15.27), ('Addis Ababa', 9.03, 38.74), ('Algiers', 36.75, 3.06), ('Casablanca', 33.57, -7.59), ('Tehran', 35.69, 51.39), ('Baghdad', 33.31, 44.37), ('Riyadh', 24.71, 46.68), ('Dubai', 25.20, 55.27), ('Tel Aviv', 32.09, 34.78),
    ('Karachi', 24.86, 67.01), ('Islamabad', 33.69, 73.04), ('Delhi', 28.61, 77.21), ('Mumbai', 19.08, 72.88), ('Bangalore', 12.97, 77.59), ('Dhaka', 23.81, 90.41), ('Kabul', 34.53, 69.17), ('Tashkent', 41.30, 69.24), ('Almaty', 43.24, 76.89),
    ('Beijing', 39.90, 116.40), ('Shanghai', 31.23, 121.47), ('Hong Kong', 22.32, 114.17), ('Chengdu', 30.57, 104.07), ('Urumqi', 43.83, 87.62), ('Lhasa', 29.65, 91.12), ('Taipei', 25.03, 121.57), ('Seoul', 37.57, 126.98), ('Pyongyang', 39.02, 125.75),
    ('Tokyo', 35.68, 139.69), ('Osaka', 34.69, 135.50), ('Vladivostok', 43.12, 131.89), ('Novosibirsk', 55.03, 82.92), ('Yekaterinburg', 56.84, 60.61), ('Murmansk', 68.97, 33.08), ('Bangkok', 13.76, 100.50), ('Hanoi', 21.03, 105.85), ('Singapore', 1.35, 103.82),
    ('Jakarta', -6.21, 106.85), ('Manila', 14.60, 120.98), ('Sydney', -33.87, 151.21), ('Melbourne', -37.81, 144.96), ('Perth', -31.95, 115.86), ('Darwin', -12.46, 130.84), ('Auckland', -36.85, 174.76), ('Wellington', -41.29, 174.78),
    ('Guam', 13.44, 144.79), ('Diego Garcia', -7.31, 72.41), ('McMurdo', -77.85, 166.67), ('Nuuk', 64.18, -51.72), ('Thule', 76.53, -68.70),
]
json.dump([[n, la, lo] for n, la, lo in CITIES], open(os.path.join(d, 'cities.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print(len(arcs), 'arcs', sum(len(a) // 2 for a in arcs), 'points;', len(CITIES), 'cities')
