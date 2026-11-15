# Architecture

Everything is deliberately simple: a Python pipeline that produces one JSON file, and one HTML template that embeds it.
No framework, no bundler, no database, no server-side code beyond a static file server.

```
 public sources ──> build/fetch_*.py ──> data/*.json, *.tle, *.csv
                                           │
                     build/parse_nrol.py, land.py, borders.py, content.py, geoid.py
                                           │
                                   build/build_data.py ──> data/data.json  (≈1 MB, every object + show content)
                                           │
                                   build/build_page.py ──> site/index.html (vendored libraries, local)
                                                       ──> dist/nro-orbit-watch.html (CDN libraries, hosted copy)
```

## Why a single embedded page

The page has to run in three places: a laptop with no internet, a wall display in a lobby, and a sandboxed frame on a
hosting site that blocks most outbound requests. Embedding the dataset means the first paint never waits on a network
call and the show never breaks because a feed is down. Live sources (launch feed, weather, imagery tiles, webcams) are
tried at runtime and fall back to the snapshot taken at build time.

## Data model

Each object in `data.json` is one tracked thing: a payload, rocket body, debris item or a whole historical program.
Key fields:

| field | meaning |
|---|---|
| `tle` | two-line element set when amateur observers have published one |
| `kep` | Keplerian elements derived from the TLE, or a representative orbit (`rep: true`) when there is none |
| `layer` | `nro`, `usother`, `allied`, `gps`; `lyr` is the display layer after hardware/unknown splitting |
| `family`, `program`, `function`, `orbit`, `siteName`, `decade` | facets used for colouring and filtering |
| `t0`, `t1` | in-orbit window in milliseconds for the timeline and timelapse |
| `model` | which icon silhouette to draw |

Representative orbits exist because the NRO does not publish orbits and amateur coverage is incomplete. They are drawn
hollow and labelled as such everywhere.

## Propagation

Near an element epoch the page runs SGP4 (satellite.js). Far from it, and for representative orbits, it uses a Keplerian
model with J2 nodal precession, which keeps the orbit shape honest while the position along the orbit drifts. At fast
time rates (timelapse, decade slides) positions follow a smooth 150x clock while the calendar runs at the chosen rate,
so satellites glide instead of jumping between random phases.

## The lobby show

A weighted random scheduler with cooldowns and a long no-repeat memory picks from about twenty segment types. Each
segment is a small object: a key, a duration, a `setup()` that configures the shared state (`S`) and shows a panel, and
an optional `tick()`. The layout code gives the panel one third of the screen and centres the globe in the rest using a
camera view offset, fitting the camera so the highest orbit on screen stays in frame. Full-screen slides (company,
weather, headlines, infographics) dim the globe or replace it with generated artwork.

## Satellite point of view

A second WebGL renderer looks straight down from the chosen satellite with an always-lit globe texture. When online it
streams Esri World Imagery tiles for the footprint, assembles them into a texture patch projected onto the sphere, and
prefetches the tiles 45 and 100 seconds ahead along the ground track so they are ready when the satellite arrives.
A canvas HUD draws brackets, reticle, readouts and a scale bar over it.

## Ambience

Background sound is synthesised in the browser with the Web Audio API (pads, arpeggios, noise beds, pings, transition
cues) from a handful of presets, so there are no audio files and nothing to license.

## Refresh

`run.py` serves `site/`, refreshes the data at startup when it is more than a day old, repeats the daily refresh every
night at 03:30, and writes `site/build.json`. The page polls that file every ten minutes and reloads itself between
lobby segments when a new build appears. A Windows scheduled task can run `run.py --refresh-data` independently.
