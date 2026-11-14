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

## Refresh the data

```
python run.py --refresh
```

Downloads the latest classified-objects element file (Mike McCants), the CelesTrak catalog and the
Wikipedia NRO launch list, rebuilds `data/data.json` and `site/index.html`, then serves.

## Layout

- `build/template.html` - the page (CSS, markup, JavaScript) with a `/*__DATA__*/` placeholder
- `build/*.py` - pipeline: fetch_inputs -> parse_nrol -> land -> build_data -> build_page
- `data/hist.json` - hand-curated pre-1996 NRO payloads (KH-11, Lacrosse, Canyon, Rhyolite, Vortex, Magnum, Jumpseat, Trumpet, Mercury, SDS, NOSS)
- `data/data.json` - merged dataset embedded in the page
- `site/` - what gets served locally; `dist/nro-orbit-watch.html` - the artifact build (CDN scripts)

## Sources

Elements: Mike McCants classfd.tle. Identities and launch dates: CelesTrak SATCAT. Missions: Wikipedia
"List of NRO launches", Gunter's Space Page. Coastlines: Natural Earth via world-atlas. Earth imagery:
NASA Blue Marble and city lights (via Wikimedia Commons and the three.js examples). Rendering: three.js r128, satellite.js 5.0.
