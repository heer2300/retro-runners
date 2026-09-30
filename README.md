# Retro-Runners

## Run locally
    python3 server.py          # then open http://127.0.0.1:8000  (Windows: python server.py)
Admin: click **Admin** (default PIN `1985` locally). Change: `RR_PIN=mysecret python3 server.py`

## Put it on Git
    git init -b main
    git add .
    git commit -m "Retro-Runners first commit"
    # create an EMPTY repo on github.com/new (no README), then:
    git remote add origin https://github.com/YOUR-USER/retro-runners.git
    git push -u origin main

## Deploy on Render (Blueprint — easiest)
1. dashboard.render.com -> **New +** -> **Blueprint** -> connect GitHub -> pick the repo.
2. Render reads `render.yaml`, shows the service + 1 GB disk -> **Apply**.
3. Wait for the deploy; your site is at `https://retro-runners.onrender.com` (or the name Render gives it).
4. Admin PIN: service -> **Environment** -> `RR_PIN` (Render generated it; you can replace it). Then use Admin on your live site.
5. Updating code later: `git add . && git commit -m "change" && git push` -> Render redeploys automatically.

Manual alternative: New + -> Web Service -> repo -> Runtime **Python**, Build `pip install -r requirements.txt`,
Start `python server.py`, Health check `/healthz`, env `RR_PIN=...`; for storage add a Disk mounted at `/var/data` and env `RR_DATA_DIR=/var/data`.

## Storage — important
- Render's filesystem is wiped on every deploy/restart unless a **persistent disk** is attached (paid plans only).
- With the disk (default `render.yaml`): edits and photos made in Admin on the live site are kept.
  The first time it starts, it copies `data/site.json` + `uploads/` from Git onto the disk. After that the disk wins.
- Free plan: edit `render.yaml` -> `plan: free`, delete the `RR_DATA_DIR` env and the `disk:` block.
  Then design the site locally (Admin), commit `data/site.json` and `uploads/`, and push. Live Admin edits are lost on redeploy/sleep.
- Move local content to a live site that already has a disk: Admin -> Backup & reset -> Export locally, Import on the live site.

## Other
- Visitors can switch theme with the **◐ Theme** button (stored in their own browser). Turn off in Admin -> General.
- Admin login locks for 5 minutes after 5 wrong PINs. The server refuses to start online with the default PIN.
- Keys: ← / → crew members, Space = jump in the game.
