import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timedelta
import random
from faker import Faker

# Setup
fake = Faker()
random.seed(42)
OUTPUT_PATH = "data/synthetic/events.csv"
RAW_DATA_PATH = "data/raw/products.csv"

def load_products():
    """Load product catalog to ensure valid product IDs"""
    print("Loading products...")
    df = pd.read_csv(RAW_DATA_PATH)
    return df['product_id'].tolist()

def generate_users(num_users=1000):
    """Generate synthetic user profiles"""
    print(f"Generating {num_users} users...")
    users = []
    personas = ['Health Nut', 'Budget Shopper', 'Parent', 'Gourmet', 'Impulse Buyer']
    
    for i in range(1, num_users + 1):
        users.append({
            'user_id': i,
            'age': random.randint(18, 75),
            'gender': random.choice(['M', 'F', 'NB']),
            'persona': random.choice(personas)
        })
    return pd.DataFrame(users)

def generate_clickstream(users_df, product_ids, num_sessions=5000):
    """Generate session-based clickstream data"""
    print(f"Simulating {num_sessions} sessions...")
    events = []
    
    user_ids = users_df['user_id'].tolist()
    
    # Start time: 30 days ago
    base_time = datetime.now() - timedelta(days=30)
    
    for _ in range(num_sessions):
        # Pick a random user and start a session
        user = random.choice(user_ids)
        session_id = str(uuid.uuid4())
        session_start = base_time + timedelta(minutes=random.randint(0, 43200)) # Random time in last 30 days
        
        # Session length: 3 to 15 interactions
        session_length = random.randint(3, 15)
        current_time = session_start
        
        # User "browsing" logic
        for _ in range(session_length):
            product = random.choice(product_ids)
            
            # 1. View Event (Always happens first)
            events.append({
                'event_id': str(uuid.uuid4()),
                'user_id': user,
                'session_id': session_id,
                'product_id': product,
                'event_type': 'view',
                'event_time': current_time,
                'device': random.choice(['mobile', 'desktop', 'tablet'])
            })
            
            # 2. Add to Cart (30% chance after view)
            if random.random() < 0.3:
                current_time += timedelta(seconds=random.randint(5, 60))
                events.append({
                    'event_id': str(uuid.uuid4()),
                    'user_id': user,
                    'session_id': session_id,
                    'product_id': product,
                    'event_type': 'cart',
                    'event_time': current_time,
                    'device': events[-1]['device'] # Same device
                })
                
                # 3. Purchase (60% chance if in cart)
                if random.random() < 0.6:
                    current_time += timedelta(seconds=random.randint(30, 120))
                    events.append({
                        'event_id': str(uuid.uuid4()),
                        'user_id': user,
                        'session_id': session_id,
                        'product_id': product,
                        'event_type': 'purchase',
                        'event_time': current_time,
                        'device': events[-1]['device']
                    })
            
            # Time between products
            current_time += timedelta(seconds=random.randint(10, 120))
            
    return pd.DataFrame(events)

if __name__ == "__main__":
    # 1. Load context
    product_ids = load_products()
    
    # 2. Create Users
    users_df = generate_users(num_users=1000)
    users_df.to_csv("data/synthetic/users.csv", index=False)
    print("Saved users.csv")
    
    # 3. Create Events
    events_df = generate_clickstream(users_df, product_ids, num_sessions=5000)
    events_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(events_df)} events to {OUTPUT_PATH}")
