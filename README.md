
## How to Run

This dashboard system consists of two main components that need to be executed sequentially:

### 1. Data Extraction and Storage (ip_staking.py)

```bash
# Install dependencies
pip install web3 pandas numpy matplotlib seaborn plotly streamlit sqlalchemy

# Run the data extraction script
python ip_staking.py
```

This script will:
- Connect to Story Mainnet
- Extract staking events (Deposit, Withdraw, Redelegate)
- Process and transform the data
- Store results in a SQLite database (staking.db)

### 2. Dashboard Visualization (run_app.py)

```bash
# Run the Streamlit dashboard
python run_app.py
```

This will:
- Start a Streamlit web server
- Set up localtunnel for external access
- Launch the dashboard in your default browser
- Display metrics and visualizations based on the staking data

Access the dashboard at the localtunnel URL displayed in the console, or at `http://localhost:8501` if accessing locally.
