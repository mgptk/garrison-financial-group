# Garrison Financial Group — Project Context

## Project Overview

A portfolio of interactive financial planning and data science tools built with Python and Streamlit, targeting financial planners and wealth managers. The goal is to demonstrate applied quantitative finance skills.

**Brand:** Garrison Financial Group
**Domain:** [gfg.finance](https://gfg.finance) — live and configured
**GitHub Pages:** Served from `/docs` on the `main` branch — live and configured
**Developer:** Experienced data scientist with CFA Level I background; fluent in Python, new to Streamlit and web deployment.

---

## Repo Structure

```
garrison-financial-group/
├── CLAUDE.md                        ← This file
├── README.md
├── .gitignore                       ← Python + Streamlit tuned
├── docs/                            ← Landing page (GitHub Pages → gfg.finance)
│   ├── index.html
│   ├── CNAME                        ← Contains "gfg.finance"
│   ├── css/style.css                ← Navy + gold design system
│   └── js/main.js
└── apps/
    ├── monte_carlo/                 ← BUILD THIS FIRST
    │   ├── app.py
    │   └── requirements.txt
    ├── portfolio_optimizer/
    │   ├── app.py
    │   └── requirements.txt
    └── macro_dashboard/
        ├── app.py
        └── requirements.txt
```

---

## Tech Stack

- **Python 3.11+**
- **Streamlit** — app framework
- **NumPy / SciPy** — simulation and optimization
- **Pandas** — data handling
- **Plotly** — all charts (interactive, consistent across apps)
- **yfinance** — price data (Portfolio Optimizer)
- **fredapi** — FRED economic data (Macro Dashboard)

---

## Deployment Architecture

| Layer | Tool | Status |
|-------|------|--------|
| Landing page | GitHub Pages (`/docs`, `main` branch) | ✅ Live at gfg.finance |
| Custom domain | gfg.finance via Cloudflare Registrar | ✅ Live |
| DNS | Cloudflare (4 A records → GitHub IPs, CNAME www) | ✅ Configured |
| App hosting | Streamlit Community Cloud (free tier) | ⏳ Pending first app |

**GitHub Pages DNS records (for reference):**
- A records on `@`: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
- CNAME on `www`: `<username>.github.io`
- Cloudflare proxy: **DNS only** (grey cloud) — required for GitHub Pages HTTPS

**Deploying a new Streamlit app:**
1. Push code to `main`
2. Go to share.streamlit.io → New app → select repo, branch `main`, path e.g. `apps/monte_carlo/app.py`
3. Add any secrets in the Streamlit Cloud dashboard (Settings → Secrets)
4. Once live, update the `href` on the relevant tool card in `docs/index.html`

---

## App Build Order

1. **Monte Carlo Retirement Simulator** ← IN PROGRESS (build this next)
2. **Macro Dashboard** (requires FRED API key)
3. **Portfolio Optimizer** (most complex, requires yfinance + scipy optimization)

---

## App 1: Monte Carlo Retirement Simulator

### Purpose
Users input retirement parameters and receive thousands of simulated outcomes with probability-of-success metrics and visualizations. A staple in financial planning and highly visual.

### All Design Decisions (finalized)

#### Simulation mechanics
- **Time step:** Monthly (scales annual inputs by /12 for mean, /√12 for vol)
- **Return distribution:** Log-normal — model log(1 + r) as normally distributed, exponentiate. Prevents negative portfolio values, reflects compounding correctly.
- **Number of simulations:** 5,000 (fast with NumPy vectorization, stable results)
- **Cholesky decomposition** for correlated stock/bond return draws

#### Asset model
- **Multi-asset: stocks + bonds split** (user sets allocation, e.g. 70/30)
- Hardcoded correlation between stocks and bonds: **−0.15** (reasonable long-run historical estimate)
- Default return/vol assumptions (nominal, annualized):
  - US Equities: 10.0% return, 17.0% volatility
  - US Bonds: 4.5% return, 7.0% volatility
- These should be editable in an "Advanced" expander — don't lead with them

#### Inflation
- Work entirely in **real (inflation-adjusted) terms** throughout
- Convert nominal returns to real: subtract inflation rate
- All dollar values on outputs are in **today's purchasing power**
- Default inflation assumption: **2.5%**, user-editable
- Label all charts clearly: "All values in today's dollars"

#### Withdrawal strategy
- **Fixed real withdrawal** — user specifies annual spending in today's dollars; that amount is withdrawn each year in retirement regardless of portfolio performance
- This is intentionally conservative and produces the most dramatic/honest simulations
- Dynamic/guardrails withdrawal is a v2 feature

#### User inputs (sidebar)
- Current age
- Current portfolio value ($)
- Annual contribution ($ per year, during accumulation phase)
- Target retirement age
- Annual spending in retirement ($ in today's dollars)
- Additional annual income in retirement (Social Security / pension, $ — offsets withdrawals; also input what age it starts)
- Plan to age (longevity horizon, default 90)
- Stock/bond allocation (slider, e.g. 70% stocks / 30% bonds)
- Inflation assumption (%, default 2.5%, in "Advanced" expander)
- Custom return/vol assumptions (in "Advanced" expander, pre-filled with defaults above)

#### Success definition (v1)
- **Primary:** Probability that portfolio never reaches $0 before plan-to age
- Secondary metrics shown alongside: median ending portfolio, 10th percentile ending portfolio
- Optional legacy floor: "I want to end with at least $X" — changes success threshold

#### Outputs / visualizations
1. **Headline success rate** — large, prominent percentage with color coding (green ≥80%, yellow 60-80%, red <60%)
2. **Fan chart** — percentile bands (10th, 25th, 50th, 75th, 90th) of portfolio value over time; shade retirement phase differently from accumulation phase; mark retirement date with a vertical line
3. **Terminal value histogram** — distribution of final portfolio values across all simulations; mark $0 with a red line
4. **Key stats table** — median outcome, best 10%, worst 10%, probability of doubling real wealth
5. **Sensitivity table** (stretch goal for v1) — success rate as retirement age, spending, or savings rate varies by ±10-20%

### Implementation Notes

```python
# Rough simulation loop structure (vectorized)
import numpy as np

def run_simulation(n_sims, n_months, monthly_mean, monthly_vol, ...):
    # Generate correlated monthly returns for stocks and bonds
    # L = cholesky([[stock_var, cov], [cov, bond_var]])
    # returns shape: (n_sims, n_months, 2) → blend by allocation
    # Accumulation phase: add monthly contribution
    # Retirement phase: subtract monthly withdrawal (net of SS income)
    # Track portfolio value each month
    # Return array of shape (n_sims, n_months)
```

- Use `@st.cache_data` on the simulation function — simulations are deterministic given a seed, so cache by input hash
- Set `np.random.seed` for reproducibility — but allow user to re-run with different seed if they want
- Plotly for all charts — consistent with the rest of the project
- Use `st.sidebar` for all inputs, main area for outputs

---

## Landing Page (docs/)

Custom hand-coded HTML/CSS — **not** a site builder. Navy + gold color scheme.

**To add a new app to the landing page:** Edit `docs/index.html` and update the relevant `<a href="#">` in the tool card to point to the Streamlit Cloud URL. No build step required — just commit and push.

**Color palette (CSS variables in style.css):**
- `--navy: #0d1b2a`
- `--navy-mid: #1b2e45`
- `--navy-light: #243b55`
- `--gold: #c9a84c`
- `--gold-light: #e0c068`

---

## Current Status

| Item | Status |
|------|--------|
| Repo scaffolded | ✅ Done |
| .gitignore, README | ✅ Done |
| Landing page (HTML/CSS/JS) | ✅ Done (placeholder app links) |
| CNAME + domain configured | ✅ Done |
| Monte Carlo — design decisions | ✅ Done (see above) |
| Monte Carlo — implementation | ⏳ Next task |
| Portfolio Optimizer | ⏳ Not started |
| Macro Dashboard | ⏳ Not started |

---

## Running Apps Locally

```bash
# From repo root, activate venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows

# Install deps for the app you're working on
pip install -r apps/monte_carlo/requirements.txt

# Run
streamlit run apps/monte_carlo/app.py
```

Streamlit hot-reloads on file save — no need to restart the server during development.
