import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

# connect to your SQLite DB
engine = create_engine("sqlite:///staking.db")

# 1. Cumulative Staked Over Time
query1 = """
SELECT 
    DATE(timestamp) AS day,
    SUM(SUM(CASE 
        WHEN event_type = 'Deposit' THEN amount 
        WHEN event_type = 'Withdraw' THEN amount
        ELSE 0 
    END)) OVER (ORDER BY DATE(timestamp)) AS cumulative_staked
FROM flow
GROUP BY day
ORDER BY day;
"""
df1 = pd.read_sql_query(query1, engine)

# 2.Total Staked
query2 = """
SELECT 
    SUM(CASE 
        WHEN event_type = 'Deposit' THEN amount 
        WHEN event_type = 'Withdraw' THEN amount
        ELSE 0 
    END) AS total_staked
FROM flow
"""
df2 = pd.read_sql_query(query2, engine)

# 3. Daily Delegators Count
query3 = """
SELECT 
    DATE(timestamp) AS day,
    COUNT(DISTINCT delegator) AS delegators
FROM flow
GROUP BY day
ORDER BY day;
"""
df3 = pd.read_sql_query(query3, engine)

# 4. Current Active Delegators
query4 = """
select count(delegator) as n 
FROM (
SELECT 
    delegator,
    SUM(amount) AS amount
FROM flow
GROUP BY 1
) t 
WHERE amount > 0 
"""
df4 = pd.read_sql_query(query4, engine)

# 5. Top Delegators
query5 = """
SELECT
    delegator,
    SUM(amount) AS staked_amount
FROM flow
GROUP BY delegator
HAVING staked_amount > 0
ORDER BY staked_amount DESC
LIMIT 50
"""
df5 = pd.read_sql_query(query5, engine)

# 6. Stake Duration Distribution
query6 = """
WITH tiered AS (
    SELECT
        CASE staking_period
            WHEN 0 THEN 'FLEXIBLE'
            WHEN 1 THEN 'SHORT'
            WHEN 2 THEN 'MEDIUM'
            WHEN 3 THEN 'LONG'
        END                 AS period_tier,
        amount              AS gross_staked
    FROM deposit
)
SELECT
    period_tier,
    SUM(gross_staked)                    AS gross_staked,
    ROUND(100.0 * SUM(gross_staked) /
          (SELECT SUM(gross_staked) FROM tiered), 2)  AS pct_share
FROM tiered
GROUP BY period_tier
ORDER BY gross_staked DESC;
"""
df6 = pd.read_sql_query(query6, engine)



# 7. Daily Stake, Unstake and Net Stake
query7 = """
SELECT
    DATE(timestamp)                                            AS day,
    SUM(CASE WHEN amount > 0 THEN  amount        ELSE 0 END)   AS daily_staked,
    SUM(CASE WHEN amount < 0 THEN amount        ELSE 0 END)    AS daily_unstaked,   
    SUM(amount)                                                AS daily_net_staked
FROM flow
GROUP BY day
ORDER BY day;
"""
df7 = pd.read_sql_query(query7, engine)

# 8. Daily New Delegators
query8 = """
WITH first_deposit_day AS (
    SELECT
        delegator,
        DATE(MIN(timestamp)) AS first_day
    FROM   flow
    WHERE  amount > 0                 -- deposits only
    GROUP  BY delegator
)

SELECT
    first_day                     AS day,
    COUNT(*)                      AS new_delegators
FROM   first_deposit_day
GROUP  BY first_day
ORDER  BY first_day;
"""
df8 = pd.read_sql_query(query8, engine)

# 9. Daily Active Delegators 
query9 = """
-- 1. Fixed date range calendar
WITH RECURSIVE calendar(day) AS (
    SELECT DATE('2025-02-11')  -- Fixed start date
    UNION ALL
    SELECT DATE(day, '+1 day')
    FROM calendar
    WHERE day < DATE('2025-05-14')  -- Fixed end date
),

-- 2. Calculate net change per delegator per day
net_daily AS (
    SELECT
        delegator,
        DATE(timestamp) AS day,
        SUM(amount) AS daily_net
    FROM flow
    GROUP BY delegator, DATE(timestamp)
),

-- 3. Calculate running balance using window function
running_balance AS (
    SELECT
        delegator,
        day,
        daily_net,
        SUM(daily_net) OVER (
            PARTITION BY delegator
            ORDER BY day
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_balance
    FROM net_daily
),

-- 4. Create a complete grid of all delegators and all days
complete_grid AS (
    SELECT
        c.day,
        d.delegator
    FROM calendar c
    CROSS JOIN (SELECT DISTINCT delegator FROM flow) d
),

-- 5. Join the running balance to the complete grid
-- and find the most recent balance for each delegator on each day
daily_balances AS (
    SELECT
        g.day,
        g.delegator,
        (
            SELECT rb.cumulative_balance
            FROM running_balance rb
            WHERE rb.delegator = g.delegator
            AND rb.day <= g.day
            ORDER BY rb.day DESC
            LIMIT 1
        ) AS current_balance
    FROM complete_grid g
)

-- 6. Count delegators with positive balance each day
SELECT
    day,
    COUNT(DISTINCT delegator) AS active_delegators
FROM daily_balances
WHERE current_balance > 0
GROUP BY day
ORDER BY day;
"""
df9 = pd.read_sql_query(query9, engine)

# 10. Top Validators Stake Share
query10 = """
/* Top-10 Validators’ Stake Share
   ──────────────────────────────
   • `flow.amount`  > 0  = Deposit   (credited to `validator`)
   • `flow.amount`  < 0  = Withdraw  (debited   from `validator`)
   • `redelegate` moves stake from `validator_src` → `validator_dst`
*/

WITH validator_deltas AS (
    /* + / − movements from the flow ledger */
    SELECT validator, amount               AS delta
    FROM   flow

    UNION ALL
    /* Redelegate: subtract from the source validator … */
    SELECT validator_src AS validator, -amount
    FROM   redelegate

    UNION ALL
    /* … and add to the destination validator */
    SELECT validator_dst AS validator,  amount
    FROM   redelegate
),

validator_balances AS (
    SELECT
        validator,
        SUM(delta) AS stake
    FROM   validator_deltas
    GROUP  BY validator
    HAVING stake > 0                       -- ignore empty / negative balances
),

total AS (
    SELECT SUM(stake) AS total_stake
    FROM   validator_balances
),

ranked AS (
    SELECT
        validator,
        stake,
        ROW_NUMBER() OVER (ORDER BY stake DESC) AS rnk
    FROM   validator_balances
)

SELECT
    validator,
    stake,
    ROUND(100.0 * stake / total_stake, 2) AS stake_pct
FROM   ranked, total
ORDER  BY stake DESC;
"""
df10 = pd.read_sql_query(query10, engine)

######################

# Streamlit layout
title = "Story Network Staking Dashboard"
st.title(title)

# Two-column layout for number metrics 
col1, col2 = st.columns(2)

with col1:
    #st.subheader("Total Staked")
    total_staked = df2["total_staked"].iloc[0]
    formatted_total = f"{total_staked:,.2f} IP"
    st.metric("Total Staked", formatted_total, border=True)


with col2:
    #st.subheader("Current Active Delegators")
    active_delegator = df4["n"].iloc[0]
    st.metric("Active Delegators", active_delegator, border=True)


# Full-width chart for total staked over time
st.subheader("Total Staked Over Time")
fig1 = px.line(df1, x="day", y="cumulative_staked")
st.plotly_chart(fig1, use_container_width=True)

# Full-width chart for Daily Stake and Unstake
import plotly.graph_objects as go

# 1. Load your example data
df = df7

# 2. Build the combo figure
fig = go.Figure()

# Staked bars
fig.add_trace(go.Bar(
    x=df["day"],
    y=df["daily_staked"],
    name="Staked",
    offsetgroup=0
))

# Unstaked bars (positive values, but colored separately)
fig.add_trace(go.Bar(
    x=df["day"],
    y=df["daily_unstaked"],
    name="Unstaked",
    offsetgroup=1
))

# Net-line
fig.add_trace(go.Scatter(
    x=df["day"],
    y=df["daily_net_staked"],
    name="Net Staked",
    mode="lines+markers",
    yaxis="y2"
))

# 3. Layout: secondary y-axis for the line
fig.update_layout(
    #title="Daily Stake, Unstake and Net Staked",
    xaxis_title="Date",
    yaxis_title="Volume (IP)",
    yaxis2=dict(
        title="Net Staked (IP)",
        overlaying="y",
        side="right"
    ),
    barmode="group",       # or "relative" for stacked
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# 4. Render in Streamlit
st.subheader("Daily Stake, Unstake and Net Staked")
st.plotly_chart(fig, use_container_width=True)



# Full-width chart for Daily Active Delegators 
st.subheader("Daily Active Delegators")
fig3 = px.line(df9, x="day", y="active_delegators")
st.plotly_chart(fig3, use_container_width=True)


# Full-width chart for Daily New Delegators
st.subheader("Daily New Delegators")
fig4 = px.line(df8, x="day", y="new_delegators")
st.plotly_chart(fig4, use_container_width=True)


# Full-width chart for Daily Delegators Count
st.subheader("Daily Delegators Count")
fig5 = px.line(df3, x="day", y="delegators")
st.plotly_chart(fig5, use_container_width=True)


# Full-width chart for stake duration distribution
st.subheader("Stake Duration Distribution")
#fig4 = px.pie(df6, values="gross_staked", names="period_tier",
#             title="Stake Duration Distribution")
fig6 = px.pie(df6, values="gross_staked", names="period_tier")
st.plotly_chart(fig6)


# Full-width chart for Top Validators Stake Share

# 1. Sort by raw stake descending
df_sorted = df10.sort_values("stake", ascending=False)

# 2. Split top-10 vs rest
top10     = df_sorted.head(10).copy()
others    = df_sorted.iloc[10:]

# 3. Sum up the rest
others_stake   = others["stake"].sum()
others_pct     = others["stake_pct"].sum()

# 4. Build the “Others” row
others_row = pd.DataFrame({
    "validator": ["Others"],
    "stake":     [others_stake],
    "stake_pct": [others_pct]
})

# 5. Concatenate and reset index
df_top10_others = pd.concat(
    [top10[["validator","stake","stake_pct"]], others_row],
    ignore_index=True
)

st.subheader("Top Validators Stake Share")
fig7 = px.pie(df_top10_others, values="stake", names="validator")
st.plotly_chart(fig7)



# Full-width chart for Top Delegators
df5["staked_amount"] = df5["staked_amount"].round(0).astype(int)
st.subheader("Top 50 Delegators Stake Amount")
st.dataframe(df5.style.format({"staked_amount": "{:,}"}))

