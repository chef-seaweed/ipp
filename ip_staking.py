# Install required packages
!pip install web3 pandas numpy matplotlib seaborn plotly streamlit
!pip install ipywidgets  
!pip install sqlalchemy sqlite3  


from web3 import Web3
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


# Connect to Story Mainnet
w3 = Web3(Web3.HTTPProvider('https://mainnet.storyrpc.io'))

# Check connection
if w3.is_connected():
    print(f"Successfully connected to Story Mainnet")
    print(f"Current block: {w3.eth.block_number}")
else:
    print("Failed to connect to Story Mainnet")

# Load ABI
def load_contract_abi(abi_path='IPTokenStaking.abi.json'):
    """Load ABI from JSON file in the Colab directory"""
    import json
    
    try:
        with open(abi_path, 'r') as f:
            abi = json.load(f)
        print(f"ABI loaded successfully from {abi_path}")
        return abi
    except Exception as e:
        print(f"Error loading ABI: {e}")
        return None

# Initialize contract
CONTRACT_ADDRESS = '0xCCcCcC0000000000000000000000000000000001' 
ABI = load_contract_abi()
# Initialize contract with the loaded ABI
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# Data Extraction Functions 
def get_events(event_name, from_block, to_block=None):
    """Get historical events from the contract"""
    if to_block is None:
        to_block = w3.eth.block_number
    
    try:
        event_filter = getattr(contract.events, event_name).create_filter(
            from_block=from_block,
            to_block=to_block
        )
        events = event_filter.get_all_entries()
        return events
    except Exception as e:
        print(f"Error getting {event_name} events: {e}")
        return []

def get_block_timestamp(block_number):
    """Get timestamp for a block number"""
    try:
        block = w3.eth.get_block(block_number)
        return datetime.fromtimestamp(block.timestamp)
    except Exception as e:
        print(f"Error getting block timestamp: {e}")
        return None

def get_block_timestamp(block_number, max_retries=3):
    """Get timestamp for a block number with retry logic"""
    for attempt in range(max_retries):
        try:
            block = w3.eth.get_block(block_number)
            return datetime.fromtimestamp(block.timestamp)
        except Exception as e:
            print(f"Attempt {attempt+1}/{max_retries}: Error getting timestamp for block {block_number}: {e}")
            import time
            time.sleep(1)  # Add delay between retries
    
    # If we've reached here, all attempts failed
    print(f"CRITICAL: Failed to get timestamp for block {block_number} after {max_retries} attempts")
    return None

# Data Collection and Processing 
# Define time range 
start_block = 837755
end_block = 4133590

# Get events - based on the ABI, we're looking at Deposit, Withdraw, and Redelegate events
deposit_events = get_events('Deposit', start_block, end_block)
withdraw_events = get_events('Withdraw', start_block, end_block)
redelegate_events = get_events('Redelegate', start_block, end_block)

print(f"Found {len(deposit_events)} Deposit events")
print(f"Found {len(withdraw_events)} Withdraw events")
print(f"Found {len(redelegate_events)} Redelegate events")

# Process Deposit events
deposit_data = []
for event in deposit_events:
    deposit_data.append({
        'event_type': 'Deposit',
        'delegator': event.args.delegator,
        'validator': '0x' + event.args.validatorCmpPubkey.hex(),  # Convert bytes to hex string for readability
        'amount': event.args.stakeAmount / 10**18,  # Convert to token units assuming 18 decimals
        'staking_period': event.args.stakingPeriod,
        'delegation_id': event.args.delegationId,
        'operator': event.args.operatorAddress,
        'block_number': event.blockNumber,
        'timestamp': get_block_timestamp(event.blockNumber),
        'transaction_hash': '0x' + event.transactionHash.hex()
    })

# Process Withdraw events
withdraw_data = []
for event in withdraw_events:
    withdraw_data.append({
        'event_type': 'Withdraw',
        'delegator': event.args.delegator,
        'validator': '0x' + event.args.validatorCmpPubkey.hex(),
        'amount': -event.args.stakeAmount / 10**18,  # Negative to show outflow
        'delegation_id': event.args.delegationId,
        'operator': event.args.operatorAddress,
        'block_number': event.blockNumber,
        'timestamp': get_block_timestamp(event.blockNumber),
        'transaction_hash': '0x' + event.transactionHash.hex()
    })

# Process Redelegate events
redelegate_data = []
for event in redelegate_events:
    redelegate_data.append({
        'event_type': 'Redelegate',
        'delegator': event.args.delegator,
        'validator_src': '0x' + event.args.validatorSrcCmpPubkey.hex(),
        'validator_dst': '0x' + event.args.validatorDstCmpPubkey.hex(),
        'delegation_id': event.args.delegationId,
        'amount': event.args.amount / 10**18,
        'operator': event.args.operatorAddress,
        'block_number': event.blockNumber,
        'timestamp': get_block_timestamp(event.blockNumber),
        'transaction_hash': '0x' + event.transactionHash.hex()
    })

# Create and return DataFrames
deposit_df = pd.DataFrame(deposit_data) if deposit_data else pd.DataFrame()
withdraw_df = pd.DataFrame(withdraw_data) if withdraw_data else pd.DataFrame()
redelegate_df = pd.DataFrame(redelegate_data) if redelegate_data else pd.DataFrame()


# For combined flow analysis (deposits and withdrawals)
if not deposit_df.empty and not withdraw_df.empty:
    flow_df = pd.concat([
        deposit_df[['event_type', 'delegator', 'validator', 'amount', 'delegation_id', 'block_number', 'timestamp', 'transaction_hash']],
        withdraw_df[['event_type', 'delegator', 'validator', 'amount', 'delegation_id', 'block_number', 'timestamp', 'transaction_hash']]
    ])
    flow_df = flow_df.sort_values('timestamp')
elif not deposit_df.empty:
    flow_df = deposit_df[['event_type', 'delegator', 'validator', 'amount', 'delegation_id', 'block_number', 'timestamp', 'transaction_hash']]
elif not withdraw_df.empty:
    flow_df = withdraw_df[['event_type', 'delegator', 'validator', 'amount', 'delegation_id', 'block_number', 'timestamp', 'transaction_hash']]
else:
    flow_df = pd.DataFrame()


# Export to CSV for potentional future use 
deposit_df.to_csv('deposit_df.csv', index=False)
withdraw_df.to_csv('withdraw_df.csv', index=False)
flow_df.to_csv('flow_df.csv', index=False)
redelegate_df.to_csv('redelegate_df.csv', index=False)


## Data Storge and Query ##

# Spin up a DB
from sqlalchemy import create_engine, text
# create a local file “staking.db”
engine = create_engine("sqlite:///staking.db")  
# write each DF to its own table
deposit_df.to_sql("deposit", engine, if_exists="replace", index=False)
withdraw_df.to_sql("withdraw", engine, if_exists="replace", index=False)
redelegate_df.to_sql("redelegate", engine, if_exists="replace", index=False)
flow_df.to_sql("flow", engine, if_exists="replace", index=False)

# Deal with missing timestamp if there's any

def fix_missing_timestamps():
    # Connect to the database
    from sqlalchemy import create_engine, text
    import pandas as pd
    
    # Create engine
    engine = create_engine("sqlite:///staking.db")
    
    # Find records with null timestamps
    query = "SELECT DISTINCT block_number FROM flow WHERE timestamp IS NULL"
    missing_blocks = pd.read_sql(query, engine)
    
    if missing_blocks.empty:
        print("No missing timestamps found in flow table")
        return
    
    print(f"Found {len(missing_blocks)} distinct blocks with missing timestamps")
    
    # Get timestamps for those blocks
    block_to_timestamp = {}
    for block_number in missing_blocks['block_number']:
        # Use our improved function with retries
        timestamp = get_block_timestamp(block_number, max_retries=5)
        if timestamp:
            block_to_timestamp[block_number] = timestamp
    
    print(f"Retrieved {len(block_to_timestamp)} timestamps successfully")
    
    # Update the database tables
    with engine.connect() as conn:
        for block_number, timestamp in block_to_timestamp.items():
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            # Update flow table
            flow_query = text(f"""
                UPDATE flow 
                SET timestamp = '{timestamp_str}'
                WHERE block_number = {block_number} AND timestamp IS NULL
            """)
            conn.execute(flow_query)
            
            # Update deposit table
            deposit_query = text(f"""
                UPDATE deposit 
                SET timestamp = '{timestamp_str}'
                WHERE block_number = {block_number} AND timestamp IS NULL
            """)
            conn.execute(deposit_query)
            
            # Update withdraw table
            withdraw_query = text(f"""
                UPDATE withdraw 
                SET timestamp = '{timestamp_str}'
                WHERE block_number = {block_number} AND timestamp IS NULL
            """)
            conn.execute(withdraw_query)
            
        conn.commit()
    
    print("Database updated successfully")

# After creating your tables
fix_missing_timestamps()

# Verify fix worked
verification_query = "SELECT COUNT(*) FROM flow WHERE timestamp IS NULL"
with engine.connect() as conn:
    result = conn.execute(text(verification_query)).scalar()
    if result == 0:
        print("All timestamps are now filled!")
    else:
        print(f"Still have {result} rows with null timestamps")