# Garrison Financial Group

Interactive financial planning and investment analysis tools built with Python and Streamlit. Designed to demonstrate applied data science in a financial context.

## Tools

| App | Description | Status |
|-----|-------------|--------|
| [Monte Carlo Retirement Simulator](apps/monte_carlo/) | Simulate thousands of retirement outcomes with probability-of-success metrics | In development |
| [Portfolio Optimizer](apps/portfolio_optimizer/) | Mean-variance optimization, efficient frontier visualization, and CVaR analysis | In development |
| [Macro Dashboard](apps/macro_dashboard/) | Live FRED economic indicators with yield curve and recession signals | In development |

## Project Structure

```
garrison-financial-group/
├── docs/                        # Landing page (served via GitHub Pages)
│   ├── index.html
│   ├── css/style.css
│   └── js/main.js
├── apps/
│   ├── monte_carlo/             # Retirement simulator
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── portfolio_optimizer/     # Markowitz optimizer
│   │   ├── app.py
│   │   └── requirements.txt
│   └── macro_dashboard/         # FRED macro indicators
│       ├── app.py
│       └── requirements.txt
├── .gitignore
└── README.md
```

## Local Development

Each app can be run independently:

```bash
# Create and activate virtual environment (do this once)
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# Install dependencies for a specific app
pip install -r apps/monte_carlo/requirements.txt

# Run the app
streamlit run apps/monte_carlo/app.py
```

## Deployment

- **Landing page**: GitHub Pages (served from `/docs`)
- **Apps**: Streamlit Community Cloud (each app deployed from its subdirectory)
- **Domain**: [gfg.finance](https://gfg.finance)

## Tech Stack

- Python 3.11+
- Streamlit
- NumPy / SciPy / Pandas
- Plotly
- FRED API (macro dashboard)
- yfinance (portfolio optimizer)
