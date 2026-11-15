# Data sources

Everything on the display comes from publicly available sources. Nothing classified, proprietary or privileged is used.

| What | Source | Script | Notes |
|---|---|---|---|
| Orbital elements for classified objects | Mike McCants' `classfd.tle` (amateur observers) | `fetch_inputs.py` | Observers time passes with binoculars and stopwatches and fit the elements; accuracy depends on how recently each object was seen |
| Catalog identities, launch and decay dates | CelesTrak SATCAT | `fetch_inputs.py` | public catalog |
| GPS constellation elements | CelesTrak `gps-ops` | `fetch_inputs.py` | shown on its own layer for the navigation explainer |
| NROL mission list, patches | Wikipedia "List of NRO launches" | `fetch_inputs.py`, `parse_nrol.py`, `fetch_mission_images.py` | wikitext parsed into rows; patch file names feed the image fetch |
| Pre-1996 payloads, program histories | Gunter's Space Page, declassified NRO histories, hand-curated | `data/hist.json`, `content.py` | representative orbits where no elements exist |
| Coastlines, borders, cities | Natural Earth via world-atlas | `land.py`, `borders.py` | 110 m resolution |
| Earth imagery | NASA Blue Marble, Black Marble (city lights) | `site/earth-*.jpg` | public domain |
| Historical and mission photographs | Wikimedia Commons | `fetch_images.py`, `fetch_mission_images.py` | only public-domain or Creative Commons files; credited on screen |
| Recent and upcoming launches | Launch Library 2 (The Space Devs) | `fetch_launches.py` | also fetched live when the page is online |
| Weather | NOAA GOES-19 imagery, National Weather Service API | `fetch_weather.py` | forecast, hourly outlook and alerts for the HQ grid point; national severe alerts |
| Headlines | Google News RSS searches | `fetch_news.py` | clustered by topic, screened against politics and controversy, shown only within 48 hours |
| Geoid | NGA EGM96 as packaged by PROJ | `geoid.py` | 15-minute grid sampled to 2 degrees |
| Imagery under the satellite view | Esri World Imagery tiles | runtime only | attribution shown on screen; not stored |
| Company information | roster5.com | `data/social.json` | pasted by hand and screened by `fetch_social.py` |

## Screening rules

- Headlines: a story must appear in at least five articles from three outlets, match an impact pattern (aviation,
  launches, severe weather, national emergencies) and contain no blocked terms (politics, crime, conflict, money
  matters, celebrity). Rejected items stay in `news.json` with the reason.
- Company posts: no profanity, politics, personnel or financial matters, contact details or addresses; under 700
  characters. Rejected posts are kept with a reason and never shown.
- Images: only files whose license is public domain or Creative Commons attribution; a handful of poor matches were
  removed by hand and the search keys retired.
