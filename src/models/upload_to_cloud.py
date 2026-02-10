import pandas as pd
from sqlalchemy import create_engine
import os

# 1. PASTE YOUR NEON CONNECTION STRING HERE
# (Ideally use an env var, but for a one-off script, pasting is fine)
NEON_URL = os.getenv("NEON_URL")

def upload_data():
    print("Connecting to Neon...")
    # SQLAlchemy requires 'postgresql://' instead of 'postgres://' sometimes
    if NEON_URL.startswith("postgres://"):
        url = NEON_URL.replace("postgres://", "postgresql://", 1)
    else:
        url = NEON_URL
        
    engine = create_engine(url)

    # 2. Upload Products
    print("Uploading Products...")
    products = pd.read_csv("data/raw/products.csv")
    # 'if_exists=append' adds to the table we created. 'chunksize' helps with speed.
    products.to_sql('products', engine, if_exists='append', index=False, chunksize=1000)
    
    # 3. Upload Users
    print("Uploading Users...")
    users = pd.read_csv("data/synthetic/users.csv")
    users.to_sql('users', engine, if_exists='append', index=False, chunksize=1000)
    
    # 4. Upload Events (This might take a minute)
    print("Uploading Events...")
    events = pd.read_csv("data/synthetic/events.csv")
    events.to_sql('events', engine, if_exists='append', index=False, chunksize=1000)
    
    print("Done! Data is live on the cloud.")

if __name__ == "__main__":
    upload_data()
