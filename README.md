# NRO Orbit Watch

Live and historical 3D/2D view of NRO reconnaissance satellites, propagated from amateur-tracked orbital elements.
Published copy: https://claude.ai/artifact/YBtYExpuJAvvPHMZmZzW6e

## Run locally

```
python run.py
```

Opens http://localhost:8787 in the browser. Everything the page needs is served from `site/`
(three.js and satellite.js are vendored, Earth imagery is local), so it works without internet
apart from the Google Fonts, which fall back to system fonts when offline.

## Lobby mode

Press **Lobby** (or open `http://localhost:8787/#lobby`) for the full-screen wall-monitor show: an intro card,
then randomly scheduled segments with a long no-repeat memory: live overviews, satellite spotlights, program files
with declassified imagery, fact cards, launch-site tours, what is overhead at Roster-5 HQ, recent and upcoming
launches (live from Launch Library 2 when reachable, otherwise the snapshot in `data/launches.json`), decade
retrospectives, fleet statistics and the cinematic timelapse. Esc or the Exit button (move the mouse) returns.

Keyboard: Space pause, H live, 1/2 globe/map, F full screen, L lobby, N next segment, T table, R reset, Esc close.

## Refresh the data

```
python run.py --refresh
```

Downloads the latest classified-objects element file (Mike McCants), the CelesTrak catalog and the
Wikipedia NRO launch list, rebuilds `data/data.json` and `site/index.html`, then serves.

## Layout

- `build/template.html` - the page (CSS, markup, JavaScript) with a `/*__DATA__*/` placeholder
- `build/*.py` - pipeline: fetch_inputs -> fetch_launches -> fetch_images -> parse_nrol -> land -> borders -> content -> build_data -> build_page
- `build/content.py` - curated program histories, launch-site notes and fact cards for the show
- `data/images.json` + `site/img/` - free-license historical images found on Wikimedia Commons (credited on screen)
- `data/hist.json` - hand-curated pre-1996 NRO payloads (KH-11, Lacrosse, Canyon, Rhyolite, Vortex, Magnum, Jumpseat, Trumpet, Mercury, SDS, NOSS)
- `data/data.json` - merged dataset embedded in the page
- `site/` - what gets served locally; `dist/nro-orbit-watch.html` - the artifact build (CDN scripts)

## Sources

Elements: Mike McCants classfd.tle. Identities and launch dates: CelesTrak SATCAT. Missions: Wikipedia
"List of NRO launches", Gunter's Space Page. Coastlines: Natural Earth via world-atlas. Earth imagery:
NASA Blue Marble and city lights (via Wikimedia Commons and the three.js examples). Rendering: three.js r128, satellite.js 5.0.
