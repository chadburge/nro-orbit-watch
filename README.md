# Roster-5 Satellite Live Viewer

A live and historical view of U.S. reconnaissance satellites, built entirely from public data, with a cinematic
wall-display mode made for the lobby at Roster-5 Software in Louisville, Colorado.

Chad Burge, 2026. All rights reserved; see [LICENSE](LICENSE).

## What it does

- **Explorer.** A 3D globe and a 2D map of every acknowledged National Reconnaissance Office satellite since 1959,
  plus allied reconnaissance, other U.S. military assets and the GPS constellation. Positions come from
  amateur-observed element sets (bright icons); objects nobody has published elements for ride representative orbits
  (hollow icons). Filter and colour by decade, role, owner, nation, orbit class, launch site and altitude; show
  footprints, cones, orbit paths and trails; scrub history; play a timelapse of every launch; point at the ground to see
  who can see it; look straight down from any satellite with streamed imagery.
- **Lobby show.** A random, no-repeat sequence of about 300 slides: live overviews with an icon key, satellite
  spotlights with real mission photos and patches, program histories, fact cards, launch sites, what is overhead at
  HQ, recent and upcoming launches with ascent paths, decades, fleet statistics, animated infographics, concept
  explainers (orbits, periapsis, inclination, the oblate Earth, the lumpy geoid, transfers, GPS), tonight's visible
  passes, weather from orbit with the local forecast, screened headlines, company and visitor slides, the cinematic
  timelapse, and a satellite's-eye view with a sensor HUD. Panels take one third of the screen and the globe the rest,
  on any aspect ratio. Optional synthesised ambience with transition cues.
- **Self-maintaining.** The server refreshes the data every night and the page reloads itself when a new build appears.

## Quick start

```
python run.py
```

Opens http://localhost:8787. Add `#lobby` to the address for the show. Everything the page needs is served from
`site/`; the only external dependency is Google Fonts, which falls back to system fonts offline.

More in [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and
[docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).

## Keeping the data fresh

| command | what it does |
|---|---|
| `python run.py` | serve; refresh first if the data is older than a day; refresh again every night at 03:30 |
| `python run.py --refresh-data` | one daily refresh (elements, catalog, launches, weather, headlines, posts) and exit |
| `python run.py --refresh` | everything, including the slow Wikimedia image passes, then serve |
| `python run.py --build` | rebuild `site/index.html` from the current `data/data.json` |

On Windows a scheduled task named "Satellite Live Viewer data refresh" runs `--refresh-data` daily at 03:30.
Results go to `data/refresh.log`.

## Sharing it without sharing the code

| command | what it does |
|---|---|
| `python tools/capture_lobby.py` | record the lobby show frame-exactly to a 4K 60 fps HEVC video (two hours or until every slide has played); `--hours 0.05` for a short test |
| `python tools/play_on_tv.py <video>` | play a rendered video on a DLNA television on the local network (`--find` lists them) |

For a live wall display, open `#lobby` in Chrome and use its Cast menu to send the tab to a Chromecast-capable TV.

## Layout

```
run.py                 server, scheduler, entry point
build/template.html    the whole page: CSS, markup, JavaScript, with a /*__DATA__*/ placeholder
build/*.py             pipeline (see docs/ARCHITECTURE.md)
data/                  inputs and the merged data.json; curated hist.json; snapshots (launches, weather, news, social)
site/                  what gets served: index.html, Earth imagery, img/ (credited Commons images), vendor/ libraries
dist/                  the hosted build (CDN libraries instead of vendored ones)
tools/                 capture_lobby.py (4K60 recording), play_on_tv.py (DLNA push)
docs/                  architecture, data sources, getting started
```

## Sources, in one line

Mike McCants' classified-objects elements, CelesTrak, Wikipedia's list of NRO launches, Gunter's Space Page, Natural
Earth, NASA Blue Marble, Wikimedia Commons, Launch Library 2, NOAA and the National Weather Service, EGM96, Esri World
Imagery. Rendering: three.js and satellite.js. Nothing classified or proprietary is used anywhere.
