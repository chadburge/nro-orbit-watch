# Usage relay

Every start of the viewer (page load, lobby start, app start, then once an hour while it runs) sends a small ping here.
The relay adds the caller's public IP address and location and appends one line to `usage/log.txt` in the private
repository `chadburge/viewer-usage`, so the owner can see whether the viewer is being used, by whom and how often,
whichever copy they are running.

Why a relay at all: the viewer runs in other people's browsers and on other machines, so it cannot carry a GitHub token.
The relay is a Cloudflare Worker (free tier, 100,000 requests a day) that holds the token as a secret.

## Deploy, once (about five minutes)

1. A Cloudflare account (free): https://dash.cloudflare.com/sign-up
2. A fine-grained GitHub token: GitHub > Settings > Developer settings > Fine-grained tokens > Generate.
   Repository access: only `viewer-usage`. Permissions: Contents, Read and write. Copy the token.
3. In this folder:

       npx wrangler login              # opens the browser once to authorise
       npx wrangler secret put GITHUB_TOKEN     # paste the token
       npx wrangler deploy

   The last command prints the relay's address, such as `https://r5-viewer-usage.<account>.workers.dev`.
4. Put that address in `USAGE_URL` in `build/template.html` and in `run.py`, rebuild (`python run.py --build`),
   commit, and republish or repackage. Leaving `USAGE_URL` empty keeps the pings switched off.

## What is logged

    time (UTC) | IP | city, region, country | mode | host | build | install id | screen | browser

- `mode`: `open` (page loaded), `lobby` (lobby show started), `server` (the app or run.py started),
  `explorer-hour` / `lobby-hour` (hourly heartbeat while running)
- `host`: where the page was served from (`localhost:8787`, a company web server, and so on)
- `install id`: a random id the browser keeps, so repeat visits from one machine can be told apart from new ones
- the recorder (`#lobby,capture`) never pings

The About page of the viewer tells users that a start-up ping is sent. The log lives in a private repository because
it contains IP addresses.
