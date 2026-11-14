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
retrospectives, fleet statistics, the cinematic timelapse, and full-screen slides: Roster-5 welcome and visitor
information, the Colorado aerospace neighborhood, Louisville history, where the data comes from, tonight's visible
passes over HQ (computed in the background from the amateur elements) and company posts from `data/social.json`.

Pop-ups own one third of the screen (the side third on wide screens, the bottom third on narrow or square ones)
and the globe is centred in the other two thirds, with the camera backed out far enough to keep the highest orbits
in frame. At fast time rates positions follow a smooth 150x clock (the calendar still runs at the chosen rate) so
satellites glide instead of jumping. Move the mouse for Back, Next, Hide-this-slide and Full-screen buttons; hidden slides are
remembered in the browser (Alt+click Hide restores them). Esc or the Exit button returns. When the page is embedded in another page (the claude.ai artifact pane), a
"Full window" button in the header and the Lobby button open it in a window of its own, where full screen works.

Keyboard: Space pause, H live, 1/2 globe/map, F full screen, L lobby, N or arrow keys next/previous segment, T table, R reset, Esc close.

Company posts: LinkedIn and the other networks block automated reading, so paste posts into `data/social_raw.json`
(id, source, date, title, text, link) and run `python build/fetch_social.py`. It screens every post (profanity,
politics, money and personnel matters, contact details, length) and only approved items reach the show.

## Refresh the data

```
python run.py --refresh
```

Downloads the latest classified-objects element file (Mike McCants), the CelesTrak catalog and the
Wikipedia NRO launch list, rebuilds `data/data.json` and `site/index.html`, then serves.

## Layout

- `build/template.html` - the page (CSS, markup, JavaScript) with a `/*__DATA__*/` placeholder
- `build/*.py` - pipeline: fetch_inputs -> fetch_launches -> fetch_images -> parse_nrol -> fetch_mission_images -> fetch_social -> land -> borders -> content -> build_data -> build_page
- `build/content.py` - curated program histories, launch-site notes and fact cards for the show
- `data/images.json` + `site/img/` - free-license images from Wikimedia Commons (credited on screen): program photos, official NROL mission patches, launch photos per mission, satellite-class and period launch-vehicle photos, tagged so each satellite gets the most specific picture available
- `data/hist.json` - hand-curated pre-1996 NRO payloads (KH-11, Lacrosse, Canyon, Rhyolite, Vortex, Magnum, Jumpseat, Trumpet, Mercury, SDS, NOSS)
- `data/data.json` - merged dataset embedded in the page
- `site/` - what gets served locally; `dist/nro-orbit-watch.html` - the artifact build (CDN scripts)

## Sources

Everything comes from publicly available sources; nothing classified or proprietary is used.
Elements: Mike McCants classfd.tle. Identities and launch dates: CelesTrak SATCAT. Missions: Wikipedia
"List of NRO launches", Gunter's Space Page. Coastlines: Natural Earth via world-atlas. Earth imagery:
NASA Blue Marble and city lights (via Wikimedia Commons and the three.js examples). Rendering: three.js r128, satellite.js 5.0.
