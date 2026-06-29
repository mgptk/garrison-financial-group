# VPS Self-Hosting Runbook — Garrison Financial Group

This is the complete, start-to-finish runbook for migrating the three Streamlit apps off Streamlit
Community Cloud (which sleeps after inactivity) onto a self-hosted Hetzner Cloud VPS. It assumes
no prior Linux server administration experience but fluency in Python and the command line.

**Integration style:** subdomain + iframe — identical to the current pattern. Each app gets its own
subdomain (`monte-carlo.gfg.finance`, etc.) running behind nginx with its own SSL certificate. The
`docs/*.html` wrapper pages stay exactly as they are today; only the iframe `src` URL changes from
`https://gfg-<name>.streamlit.app` to `https://<name>.gfg.finance`. **No changes to any `app.py`,
`docs/index.html`, or `docs/css/style.css` are required.**

---

## Decisions to lock in before you start

| Decision | Recommendation | Why |
|---|---|---|
| **Server provider** | Hetzner Cloud (already chosen) | Cheapest reliable VPS provider with a clean UI; EU company, GDPR-friendly |
| **Instance type** | CX22 (2 vCPU / 4 GB RAM / 40 GB disk) — ~€4.59/mo (~$5/mo) | All three Streamlit apps are lightweight; 4 GB comfortably runs all three plus nginx |
| **Region/location** | Ashburn, VA (US East) if available on your account, otherwise Hillsboro, OR (US East/West) | Your audience (US financial planners/wealth managers) gets lower latency than an EU region. Note: not all Hetzner accounts have US locations enabled — see Part 1 |
| **OS image** | Ubuntu 24.04 LTS | Long support window, default Python 3.12, most tutorials/AI assistance assume Ubuntu |
| **Subdomains** | `monte-carlo.gfg.finance`, `optimizer.gfg.finance`, `macro.gfg.finance` | Mirrors your existing `docs/<name>.html` naming |
| **Internal ports** | 8501 / 8502 / 8503 (localhost-only) | Streamlit's default port, incrementing per app; never exposed to the internet directly |
| **Deploy method** | Manual `git pull` + restart via a small shell script (this runbook builds it) | CI/CD (GitHub Actions → SSH deploy) is a nice v2 upgrade once you're comfortable with the basics — not needed for a 3-app personal project |
| **Secrets** | `.streamlit/secrets.toml` created by hand on the server, never committed to git | Same mechanism you already use locally; Streamlit Cloud's secrets UI goes away, but `st.secrets` keeps working unchanged |

---

## Architecture after migration

```
                          ┌─────────────────────────┐
                          │   Cloudflare DNS only    │
                          │  (grey cloud, no proxy)  │
                          └─────────────┬────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
   gfg.finance                monte-carlo.gfg.finance         optimizer.gfg.finance, macro.gfg.finance
        │                               │                               │
   GitHub Pages                  Hetzner VPS (nginx :443)       Hetzner VPS (nginx :443)
   (unchanged)                          │                               │
                              proxy → 127.0.0.1:8501          proxy → 127.0.0.1:8502 / :8503
                                        │                               │
                              systemd: monte-carlo.service    systemd: portfolio.service / macro.service
```

The landing page (`gfg.finance`) keeps living on GitHub Pages exactly as it does today — only the
three app subdomains move to the VPS. `docs/<name>.html` wrapper pages are unchanged except for the
iframe `src`.

---

## Part 0 — Prerequisites

1. **An SSH key pair.** If you don't already have one:
   ```bash
   ssh-keygen -t ed25519 -C "michael@gfg-vps"
   ```
   This creates `~/.ssh/id_ed25519` (private — never share) and `~/.ssh/id_ed25519.pub` (public —
   you'll paste this into Hetzner).
2. A Hetzner Cloud account (console.hetzner.cloud) with a payment method attached.
3. Access to your Cloudflare account for `gfg.finance` DNS.
4. Your FRED API key (the one currently in Streamlit Cloud's secrets).

---

## Part 1 — Provision the server

1. In the Hetzner Cloud console, create a new **Project** (e.g. "garrison-financial-group").
2. Click **Add Server**.
3. **Location:** pick a US region if your account offers one (Ashburn, VA / Hillsboro, OR). If
   you only see EU regions (Nuremberg, Falkenstein, Helsinki), that's fine too — Hetzner's US
   locations require a separate account approval step the first time you use them. EU works,
   visitors just get an extra ~80-100ms latency, which is unnoticeable for these apps.
4. **Image:** Ubuntu 24.04.
5. **Type:** Shared vCPU → CX22.
6. **Volume:** skip — the included 40 GB disk is plenty.
7. **Network:** leave default (public IPv4 + IPv6).
8. **SSH keys:** click "Add SSH key", paste the contents of `~/.ssh/id_ed25519.pub`, give it a
   name. This lets you log in without a password from the very first boot.
9. **Firewalls:** click "Create Firewall", allow inbound TCP 22 (SSH), 80 (HTTP), 443 (HTTPS) from
   `0.0.0.0/0` and `::/0`. Attach it to this server. (We'll also run `ufw` on the server itself as a
   second layer — defense in depth costs nothing.)
10. **Name:** `gfg-vps-01`.
11. Click **Create & Buy now**. Note the public IPv4 address once it boots (e.g. `203.0.113.45`) —
    you'll need it repeatedly below.

---

## Part 2 — First login and hardening

SSH in as root the first time:

```bash
ssh root@<server-ip>
```

### 2.1 Create a non-root sudo user

Never run apps as root day-to-day.

```bash
adduser michael
usermod -aG sudo michael

# copy your SSH key to the new user
rsync --archive --chown=michael:michael ~/.ssh /home/michael
```

### 2.2 Lock down SSH

Edit `/etc/ssh/sshd_config`:

```bash
nano /etc/ssh/sshd_config
```

Set/confirm these values:

```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Restart SSH and **open a second terminal** to confirm `ssh michael@<server-ip>` still works
*before* closing your root session (so you don't lock yourself out):

```bash
systemctl restart sshd
```

From now on, log in as `michael@<server-ip>`, and use `sudo` for privileged commands.

### 2.3 Firewall (ufw)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

### 2.4 fail2ban (blocks brute-force SSH attempts)

```bash
sudo apt update
sudo apt install -y fail2ban
sudo systemctl enable --now fail2ban
```

### 2.5 Automatic security patches

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades   # choose "Yes"
```

---

## Part 3 — Install base software

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip nginx git certbot python3-certbot-nginx
```

Confirm versions:

```bash
python3 --version   # 3.12.x on Ubuntu 24.04
nginx -v
```

---

## Part 4 — Deploy the app code

### 4.1 Clone the repo

```bash
sudo mkdir -p /opt/gfg
sudo chown michael:michael /opt/gfg
git clone https://github.com/mgptk/garrison-financial-group.git /opt/gfg
cd /opt/gfg
```

### 4.2 Create a virtual environment per app

Separate venvs avoid dependency clashes between apps (e.g. if Portfolio Optimizer and Macro
Dashboard ever need conflicting library versions).

```bash
cd /opt/gfg/apps/monte_carlo
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

cd /opt/gfg/apps/portfolio_optimizer
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

cd /opt/gfg/apps/macro_dashboard
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

### 4.3 Add the FRED secret (Macro Dashboard only)

Streamlit Cloud's Secrets UI doesn't exist on a VPS — recreate the same file by hand:

```bash
mkdir -p /opt/gfg/apps/macro_dashboard/.streamlit
nano /opt/gfg/apps/macro_dashboard/.streamlit/secrets.toml
```

Contents:

```toml
FRED_API_KEY = "your_key_here"
```

This file is already excluded by `.gitignore`, so it's safe to leave here — it will never be
committed or overwritten by `git pull`.

### 4.4 systemd service per app

systemd keeps each app running, restarts it if it crashes, and starts it automatically on reboot.

```bash
sudo nano /etc/systemd/system/monte-carlo.service
```

```ini
[Unit]
Description=GFG Monte Carlo Retirement Simulator
After=network.target

[Service]
Type=simple
User=michael
WorkingDirectory=/opt/gfg/apps/monte_carlo
ExecStart=/opt/gfg/apps/monte_carlo/.venv/bin/streamlit run app.py \
    --server.port=8501 \
    --server.address=127.0.0.1 \
    --server.headless=true \
    --browser.gatherUsageStats=false
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Repeat for the other two apps (`portfolio-optimizer.service` on port `8502`, working directory
`/opt/gfg/apps/portfolio_optimizer`; `macro-dashboard.service` on port `8503`, working directory
`/opt/gfg/apps/macro_dashboard`).

`--server.address=127.0.0.1` is the important bit — it means Streamlit only listens on localhost
and is **never reachable directly from the internet**, only via nginx.

Enable and start all three:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now monte-carlo.service
sudo systemctl enable --now portfolio-optimizer.service
sudo systemctl enable --now macro-dashboard.service

# confirm all three are "active (running)"
sudo systemctl status monte-carlo.service
```

If a service fails to start, check logs with `sudo journalctl -u monte-carlo.service -n 50 --no-pager`.

---

## Part 5 — DNS records (Cloudflare)

Add three new A records, pointing each subdomain at the VPS's public IP — exactly the same
**DNS-only (grey cloud)** setting you used for the apex domain, since nginx will be handling SSL
itself via Certbot rather than Cloudflare's proxy.

| Type | Name | Content | Proxy status |
|---|---|---|---|
| A | `monte-carlo` | `<server-ip>` | DNS only |
| A | `optimizer` | `<server-ip>` | DNS only |
| A | `macro` | `<server-ip>` | DNS only |

DNS propagation is usually under 5 minutes given Cloudflare's low TTLs. Confirm with:

```bash
dig monte-carlo.gfg.finance +short
```

---

## Part 6 — nginx reverse proxy with websocket support

Streamlit uses websockets for live updates — the proxy config must explicitly upgrade the
connection or the app will load but feel broken (widgets won't update).

```bash
sudo nano /etc/nginx/sites-available/monte-carlo.gfg.finance
```

```nginx
server {
    listen 80;
    server_name monte-carlo.gfg.finance;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Repeat for `optimizer.gfg.finance` (→ `127.0.0.1:8502`) and `macro.gfg.finance` (→ `127.0.0.1:8503`),
each as its own file in `sites-available`.

Enable all three and reload nginx:

```bash
sudo ln -s /etc/nginx/sites-available/monte-carlo.gfg.finance /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/optimizer.gfg.finance /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/macro.gfg.finance /etc/nginx/sites-enabled/

sudo nginx -t      # syntax check — must say "syntax is ok" before reloading
sudo systemctl reload nginx
```

At this point each subdomain should load the app over plain HTTP — visit
`http://monte-carlo.gfg.finance` to confirm before moving to SSL.

---

## Part 7 — SSL via Certbot

Certbot auto-edits the nginx configs above to add HTTPS and a redirect from HTTP, and sets up
auto-renewal.

```bash
sudo certbot --nginx -d monte-carlo.gfg.finance -d optimizer.gfg.finance -d macro.gfg.finance
```

Follow the prompts (enter your email, agree to terms, choose "Redirect" when asked whether to
redirect HTTP to HTTPS). Certbot installs a systemd timer that renews certificates automatically
— no recurring manual work.

Confirm renewal works (dry run, doesn't actually renew):

```bash
sudo certbot renew --dry-run
```

All three subdomains should now load over `https://` with a valid certificate.

---

## Part 8 — Point the iframes at the new subdomains

This is the only code change in the entire migration. In each wrapper page, swap the iframe `src`:

`docs/monte-carlo.html`:
```diff
- src="https://gfg-monte-carlo.streamlit.app/?embed=true"
+ src="https://monte-carlo.gfg.finance/?embed=true"
```

`docs/portfolio-optimizer.html`:
```diff
- src="https://gfg-portfolio-optimizer.streamlit.app/?embed=true"
+ src="https://optimizer.gfg.finance/?embed=true"
```

`docs/macro-dashboard.html`:
```diff
- src="https://gfg-macro-dashboard.streamlit.app/?embed=true"
+ src="https://macro.gfg.finance/?embed=true"
```

Commit and push — GitHub Pages updates in about a minute. `?embed=true` still works identically;
it's a Streamlit query-param feature, not something tied to Streamlit Cloud.

Once you've confirmed all three apps work from `gfg.finance`, you can pause or delete the old apps
on Streamlit Community Cloud (share.streamlit.io → app → Settings → Delete app) to avoid any
confusion about which deployment is live.

---

## Part 9 — Future updates (deploy workflow)

Since there's no CI/CD yet, redeploying after a code change is a manual `git pull` + service
restart. A tiny script makes this a one-liner instead of five commands:

```bash
nano /opt/gfg/deploy.sh
```

```bash
#!/usr/bin/env bash
set -euo pipefail

cd /opt/gfg
git pull origin main

for app in monte_carlo portfolio_optimizer macro_dashboard; do
    echo "Updating $app..."
    /opt/gfg/apps/$app/.venv/bin/pip install -r /opt/gfg/apps/$app/requirements.txt --quiet
done

sudo systemctl restart monte-carlo.service
sudo systemctl restart portfolio-optimizer.service
sudo systemctl restart macro-dashboard.service

echo "Done. Checking status..."
sudo systemctl is-active monte-carlo.service portfolio-optimizer.service macro-dashboard.service
```

```bash
chmod +x /opt/gfg/deploy.sh
```

From now on, after pushing a change to GitHub:

```bash
ssh michael@<server-ip> '/opt/gfg/deploy.sh'
```

This restarts all three apps every time even if you only changed one — fine at this scale (each
restart takes a couple of seconds), and simpler than tracking which app changed. You can optimize
this later if it ever bothers you.

---

## Part 10 — Ongoing maintenance

- **Logs:** `sudo journalctl -u monte-carlo.service -f` (live-tail; swap the unit name for the
  other apps). `sudo tail -f /var/log/nginx/error.log` for proxy-level issues.
- **Disk/memory check:** `df -h` and `free -h` occasionally — 3 Streamlit apps + nginx should sit
  comfortably under 1 GB RAM at idle on a 4 GB box.
- **Reboot safety:** all three systemd services and nginx are enabled to start on boot
  (`enable --now` above already did this), so a Hetzner host reboot/maintenance event recovers on
  its own.
- **Backups:** Hetzner offers automated snapshots for ~20% of the server cost/month — worth
  turning on (Server → Backups tab) given how cheap the box is. Recovery is just "restore snapshot"
  if anything goes badly wrong; you can always also just re-run this entire runbook from scratch on
  a fresh server in under an hour since everything is scripted/documented.
- **Renewing SSL:** automatic via the certbot systemd timer (`systemctl list-timers | grep certbot`
  to confirm it's scheduled).

---

## Cost summary

| Item | Cost |
|---|---|
| Hetzner CX22 | ~€4.59/mo (~$5/mo) |
| Automated snapshots (optional, recommended) | ~€0.92/mo (~$1/mo) |
| Domain (gfg.finance, already owned) | $0 incremental |
| SSL (Let's Encrypt via Certbot) | Free |
| **Total** | **~$5-6/mo**, replacing $0 (but sleeping) Streamlit Cloud free tier |

---

## Rollback plan

If anything goes wrong mid-migration, the old Streamlit Cloud deployments keep running untouched
the entire time (Parts 1–7 don't touch `docs/*.html` at all). Only Part 8 — the iframe `src`
change — actually cuts traffic over, and it's a one-line `git revert` per file if you need to back
out:

```bash
git revert <commit-hash>
git push
```

GitHub Pages updates within a minute and the wrapper pages point back at Streamlit Cloud.
