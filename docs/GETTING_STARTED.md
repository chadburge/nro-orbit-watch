# Getting started

## Run it

```
git clone <repo>
cd nro-orbit-watch
python run.py
```

Python 3.11 with Pillow is enough (`pip install pillow`). The first run rebuilds `site/index.html` if it is missing and
opens http://localhost:8787. No other dependencies; three.js and satellite.js are vendored in `site/vendor/`.

## Explore

- Drag to rotate, scroll to zoom, click a satellite for its dossier, click a launch pad to see only its launches.
- Filters on the left: layers, colour-by facet, decade, function, owner, nation, orbit class, launch site, altitude.
- Display options: footprints and cones, orbit paths (none, recent trail, full), labels, art style (realistic,
  hyper-real, cartoon, flat, night lights, blueprint, neon, monochrome, chart paper), true or compressed spacing.
- Timeline at the bottom scrubs history; Timelapse plays every launch since 1959.
- Satellite view: select a satellite and press the button in its dossier to look straight down from it.
- Point at the ground to see which satellites have that spot above their horizon.

## Lobby mode

Press Lobby (or open `/#lobby`). Move the mouse for Back, Next, Hide this slide, Full screen and Sound. Press Esc to
leave. Hidden slides are remembered on that browser; Alt+click Hide restores them. Press M for sound, which is
synthesised in the browser; the choice is remembered and resumes on the first click after a reload.

## Keep the data fresh

- `python run.py` refreshes at startup when the data is older than a day and again every night at 03:30 while it runs.
- `python run.py --refresh-data` does one daily refresh and exits; schedule it with Task Scheduler (Windows) or cron.
- `python run.py --refresh` does everything including the slow image passes (hours, because Wikimedia Commons is
  rate-limited).
- Results are logged to `data/refresh.log`; the page reloads itself between lobby segments when a new build appears.

## Host it

`dist/nro-orbit-watch.html` plus `site/earth-*.jpg` and `site/img/` is a complete static site. Copy them to any web
server or static host. Live features (launch feed, weather, imagery tiles, webcams) work when the host allows outbound
requests; otherwise the page uses the snapshots inside it. To refresh a hosted copy, run the pipeline and upload the new
`dist/` file and any new images.

## Customise

- `build/content.py` holds the program histories, fact cards, launch-site notes and concept explainers.
- `data/social_raw.json` holds company posts (see `build/fetch_social.py`).
- The HQ marker, company name and location live near the top of `build/template.html` (`HQ`, the lobby title block).
- Lobby timing, cooldowns and segment weights live in the `SEGMENTS` and `COOLDOWN` tables in the template.
