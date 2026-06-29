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
