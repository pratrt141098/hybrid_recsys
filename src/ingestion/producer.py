import pandas as pd
import redis
import json
import time
import random
import os

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
STREAM_KEY = "events_stream"
DATA_PATH = "data/synthetic/events.csv"

def run_producer():
    print(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}...")
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        print("Connected to Redis!")
    except redis.ConnectionError:
        print("Could not connect to Redis. Is the container running?")
        return

    # Load a sample of events to replay
    print("Loading events...")
    df = pd.read_csv(DATA_PATH)
    
    # Convert timestamps to strings for JSON serialization
    df['event_time'] = df['event_time'].astype(str)
    
    records = df.to_dict(orient='records')
    print(f"Loaded {len(records)} events. Starting stream...")

    while True:
        # Simulate variable traffic (10-50 events per batch)
        batch_size = random.randint(10, 50)
        batch = random.choices(records, k=batch_size)
        
        pipeline = r.pipeline()
        for event in batch:
            # Add metadata for "live" feel
            event['ingestion_time'] = time.time()
            
            # Redis Streams requires string keys/values
            # We use '*' as the ID so Redis generates a timestamp-based ID
            pipeline.xadd(STREAM_KEY, {'data': json.dumps(event)})
            
        pipeline.execute()
        print(f"Pushed {batch_size} events to {STREAM_KEY}")
        
        # Sleep to simulate real-time (0.5 to 2 seconds)
        time.sleep(random.uniform(0.5, 2.0))

if __name__ == "__main__":
    run_producer()
