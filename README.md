# IP Staking Dashboard

## Live Demo

**[Access the live dashboard demo →](https://7brm2vhqya639ncgytjfe4.streamlit.app/)**

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

## System Architecture

The IP Staking Token Flow Dashboard system is designed with a three-tier architecture:

1. **Data Extraction Layer**
   - Connects to Story Mainnet via RPC endpoint
   - Retrieves blockchain events (Deposit, Withdraw, Redelegate) from the IPTokenStaking contract
   - Processes raw event data into structured formats

2. **Data Storage Layer**
   - Stores processed event data in a relational database
   - Enables efficient querying and aggregation for metrics calculation
   - Maintains historical data for trend analysis

3. **Visualization Layer**
   - Queries the database to calculate key metrics
   - Renders interactive dashboard components
   - Presents insights through charts and key performance indicators

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│                     │     │                     │     │                     │
│  Data Extraction    │     │   Data Storage      │     │   Visualization     │
│                     │     │                     │     │                     │
│  - RPC Connection   │ ──> │  - SQLite Database  │ ──> │  - Streamlit App    │
│  - Event Processing │     │  - Data Tables      │     │  - Plotly Charts    │
│  - Data Cleaning    │     │  - SQL Queries      │     │  - Metrics Display  │
│                     │     │                     │     │                     │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

## Technology Stack

### Data Extraction
- **Web3.py**: Python library for interacting with Ethereum-compatible blockchains
- **Pandas**: Data manipulation and transformation library
- **Python datetime**: For timestamp processing and conversions

### Data Storage
- **SQLite**: Lightweight relational database for data storage
- **SQLAlchemy**: SQL toolkit and ORM for database operations

### Data Processing & Analysis
- **Pandas**: Advanced data analysis and manipulation
- **NumPy**: Numerical operations and calculations

### Visualization
- **Streamlit**: Web application framework for creating interactive dashboards
- **Plotly**: Interactive, publication-quality graphs and charts
- **Localtunnel**: Exposes local server to the internet for demonstration purposes

## Future-Production Considerations

### Data Ingestion
- **Incremental Updates**: Replace full historical scans with incremental event fetching using `fromBlock=lastBlock+1` pattern
- **Event Subscription**: Implement WebSocket connections for real-time event monitoring instead of polling
- **Error Handling**: Add robust error recovery mechanisms with automatic retries and checkpointing
- **Event Signature Monitoring**: Watch for contract upgrades that might change event signatures

### Data Storage
- **Database Scaling**: Migrate from SQLite to PostgreSQL or DuckDB for higher concurrency and volume
- **Data Partitioning**: Implement time-based partitioning for efficient querying of recent vs. historical data
- **Read Replicas**: Set up read replicas to separate analytics queries from real-time data ingestion
- **Backups**: Implement automated backup strategies with point-in-time recovery capabilities

### Processing Pipeline
- **Orchestration**: Replace manual execution with Apache Airflow or GitHub Actions for scheduled pipeline runs
- **Data Quality Checks**: Implement automated validation of event data integrity and consistency
- **Alerting**: Add monitoring for pipeline failures or unusual patterns in the data
- **Logging**: Enhanced logging for easier debugging and audit purposes

### Dashboard Deployment
- **Hosted Solution**: Deploy dashboard on Streamlit Cloud or similar service for public accessibility
- **Authentication**: Add user authentication for sensitive metrics or admin features
- **Caching**: Implement query result caching to improve dashboard performance
- **API Endpoints**: Create REST API endpoints for programmatic access to key metrics

### Performance Optimization
- **Query Optimization**: Create materialized views for frequently accessed metrics to reduce calculation overhead
- **Index Tuning**: Add specialized indexes based on common query patterns
- **Batch Processing**: Group transactions for more efficient database operations
- **Resource Scaling**: Implement auto-scaling based on user traffic and data processing needs

## Metrics Definition
> **Note on Unbonding Period:** The metrics in this dashboard does not account for the 14-day unbonding period. When a withdrawal is initiated, the tokens are immediately counted as unstaked in our metrics, though they remain locked in the protocol during the unbonding period before becoming transferable to the delegator.

| Metric | Definition | Calculation Method |
|--------|------------|-------------------|
| Total Staked | The net amount of IP tokens currently locked in the staking contract | Sum of all deposits minus sum of all withdrawals across the entire flow table |
| Total Staked Over Time | Cumulative net staked amount tracked daily | Running sum of daily net stake changes (deposits minus withdrawals) over time |
| Active Delegators | Count of unique addresses with positive stake balance | Count of distinct delegators where their cumulative stake balance is greater than zero |
| Daily New Delegators | Number of unique delegators making their first deposit on a given day | Identifying each delegator's first deposit date and counting how many first-time delegators appear each day |
| Daily Delegators Count | Number of unique delegators active (making any transaction) each day | Count of distinct delegators performing any staking-related transaction (deposit or withdrawal) per day |
| Daily Active Delegators | Number of unique delegators with positive stake balance on each day | For each calendar day, counting delegators whose cumulative balance up to that day remains positive |
| Daily Stake and Unstake | Volume of tokens staked and unstaked per day | Aggregating daily deposit amounts and withdrawal amounts, also calculating net daily movement |
| Top Delegators by Amount | Ranking of delegators with largest stake amounts | Summing each delegator's net stake (deposits minus withdrawals), filtering for positive balances, and ranking by total amount |
| Stake Duration Distribution | Distribution of staked tokens across different staking period tiers | Categorizing deposits into tiers (FLEXIBLE, SHORT, MEDIUM, LONG) based on staking_period value, then calculating amount and percentage in each tier |
| Top Validators Stake Share | Distribution of staked tokens across validators | Calculating net stake per validator by accounting for deposits, withdrawals, and redelegations (source and destination adjustments), then showing top validators' percentage share with remainder grouped as "Others" |

## Data Model

The data model in `staking.db` consists of four primary tables derived from blockchain events:

### 1. Deposit Table
| Column Name      | Data Type | Description                                      |
|------------------|-----------|--------------------------------------------------|
| event_type       | TEXT      | Type of event (always "Deposit")                 |
| delegator        | TEXT      | Address of the delegator                         |
| validator        | TEXT      | Validator compressed public key                  |
| amount           | REAL      | Amount of tokens staked (in token units)         |
| staking_period   | INTEGER   | Duration of the staking period                   |
| delegation_id    | INTEGER   | Unique identifier for the delegation             |
| operator         | TEXT      | Address of the operator                          |
| block_number     | INTEGER   | Block number where the event occurred            |
| timestamp        | TIMESTAMP | Timestamp when the event occurred                |
| transaction_hash | TEXT      | Hash of the transaction containing the event     |

### 2. Withdraw Table
| Column Name      | Data Type | Description                                      |
|------------------|-----------|--------------------------------------------------|
| event_type       | TEXT      | Type of event (always "Withdraw")                |
| delegator        | TEXT      | Address of the delegator                         |
| validator        | TEXT      | Validator compressed public key                  |
| amount           | REAL      | Amount of tokens withdrawn (negative value)      |
| delegation_id    | INTEGER   | Unique identifier for the delegation             |
| operator         | TEXT      | Address of the operator                          |
| block_number     | INTEGER   | Block number where the event occurred            |
| timestamp        | TIMESTAMP | Timestamp when the event occurred                |
| transaction_hash | TEXT      | Hash of the transaction containing the event     |

### 3. Redelegate Table
| Column Name      | Data Type | Description                                      |
|------------------|-----------|--------------------------------------------------|
| event_type       | TEXT      | Type of event (always "Redelegate")              |
| delegator        | TEXT      | Address of the delegator                         |
| validator_src    | TEXT      | Source validator compressed public key           |
| validator_dst    | TEXT      | Destination validator compressed public key      |
| delegation_id    | INTEGER   | Unique identifier for the delegation             |
| amount           | REAL      | Amount of tokens redelegated                     |
| operator         | TEXT      | Address of the operator                          |
| block_number     | INTEGER   | Block number where the event occurred            |
| timestamp        | TIMESTAMP | Timestamp when the event occurred                |
| transaction_hash | TEXT      | Hash of the transaction containing the event     |

### 4. Flow Table (Combined)
| Column Name      | Data Type | Description                                      |
|------------------|-----------|--------------------------------------------------|
| event_type       | TEXT      | Type of event (Deposit or Withdraw)              |
| delegator        | TEXT      | Address of the delegator                         |
| validator        | TEXT      | Validator compressed public key                  |
| amount           | REAL      | Amount of tokens (positive for Deposit, negative for Withdraw) |
| delegation_id    | INTEGER   | Unique identifier for the delegation             |
| block_number     | INTEGER   | Block number where the event occurred            |
| timestamp        | TIMESTAMP | Timestamp when the event occurred                |
| transaction_hash | TEXT      | Hash of the transaction containing the event     |

This data model allows for efficient analysis of token flows, staking patterns, and validator performance across the Story Mainnet IP Staking ecosystem.


## Analysis Report 

### Total Staked Over Time

**Findings**

The chart shows a clear, stepwise growth pattern in total staked over time. There are several periods of rapid inflow—most notably in late February, early-March, late-April and early May—where staking amounts jump sharply, likely driven by key protocol events or campaigns. Between these spikes, the growth is steady but slower, and there are no major prolonged declines. Overall, this suggests strong user confidence, with periodic boosts from specific catalysts.

**Why track this metric?**

Tracking Total Staked Over Time reveals overall trust and engagement trends in the network. It helps identify periods of growth or concern, shows the impact of protocol changes or incentives, and provides a clear signal of the network’s security and health trajectory

### Daily Stake, Unstake and Net Staked

**Findings**

The dataset shows a few days with very large staking inflows—most notably on March 5 (~189M IP), April 25 (~61M), and February 21 (~30M). The biggest single-day unstake happened on April 14 (~5M IP). Most days are net positive, but there are 16 days where more was unstaked than staked; the largest single-day net outflow is around –3M IP. Overall, inflows far outweigh outflows, with net staking strongly positive on most days and only occasional, relatively modest withdrawals. 

**Why track this metric?**

Tracking daily stake and unstake helps the network quickly spot changes in user confidence, assess the impact of events or incentives, and detect unusual outflows that could signal emerging risks.

### Daily Active Delegators

**Findings**

The number of active delegators grew rapidly from just 1 at launch to over 500 by the end of the period. The biggest single-day jump (+178) happened on March 3, and the largest daily decrease (–10) was minor by comparison. Overall, the trend is strongly upward, indicating a healthy and expanding staking community.

**Why track this metric?**

Tracking daily active delegators helps measure user engagement and decentralization, showing whether more unique participants are contributing to the network’s security. 



### Daily New Delegators

**Findings**

A total of 587 new delegators joined during the period, with the largest influx (178 new delegators) on March 3. No days recorded zero new delegators, and 37 newcomers joined in the most recent week, indicating continued growth and steady onboarding.

**Why track this metric?**

Tracking daily new delegators highlights onboarding momentum and the effectiveness of outreach or incentive campaigns. 

### Stake Duration Distribution

**Findings**

The vast majority of tokens (over 93%) are staked in the FLEXIBLE tier, while the MEDIUM tier accounts for just over 6%. SHORT and LONG lockups combined represent less than half a percent. This distribution shows a strong user preference for liquidity and flexibility over long-term commitment.

**Why track this metric?**
 Tracking stake duration distribution helps protocols understand user risk appetite, adjust incentive structures, and monitor the stickiness of staked capital

### Top Validators Stake Share

**Findings**

The top validator alone controls just over 10% of total stake. The top 10 validators combined hold about 45%, while the remaining validators (“Others”) collectively account for over 55% of the staked tokens. This suggests a reasonably decentralized stake distribution, though the top entities still hold significant influence.

**Why track this metric?**
 Tracking validator stake share helps monitor decentralization and security risks. High concentration may increase the risk of collusion or single points of failure, while a more even spread indicates stronger, more resilient network security

### Overview & Conclusion

Story Network shows impressive early growth and engagement: total staked has climbed rapidly, active and new delegators are steadily increasing, and stake distribution across validators remains reasonably decentralized. The majority of capital is currently held in flexible staking, indicating a user base that values liquidity and low exit barriers. Most days see positive net inflows, with only minor, isolated outflows—evidence of strong confidence and network health.

**Advice to team**

- **Build on Positive Momentum:** The continued growth in staked capital and delegator participation is a signal to keep reinforcing community trust and expanding outreach.
- **Address Flexibility Bias:** With most stake in flexible terms, consider adjusting incentives to encourage longer lockups. This will help improve network security and align with long-term growth.
- **Monitor Validator Distribution:** Although decentralization is good, keep an eye on top validator concentration. Proactively encourage stake migration to smaller validators to prevent centralization risks.
- **React to Outflows:** Even small periods of net outflow can be early warnings; continue real-time monitoring so you can quickly diagnose and respond to sudden changes in user sentiment.

**Future Analytic Improvements**

- **Track Retention Cohorts:** Analyze how long new delegators keep their stake and whether different cohorts behave differently.
- **Incorporate Unbonding Period:** Include the 14-day unbonding period to better align with the official numbers.

- **Stake Ratio:** Track total staked as a % of circulating supply to benchmark security against other chains.
- **Validator Commission Rates:** Analyze whether commission changes impact stake flow or delegator migration.
- **Net Stake Flow by Segment:** Break down stake/unstake by delegator type (new, returning, whales, etc.).
- **On-Chain Governance Participation:** Cross-reference delegators and validators with governance activity to understand true network engagement.
- **Slashing & Performance Metrics:** Include validator uptime, missed blocks, and slashing events for a full security health dashboard.
