import redis
import json
import os
import time

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
STREAM_KEY = "events_stream"
GROUP_NAME = "recsys_group"
CONSUMER_NAME = "consumer_1"

def run_consumer():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    
    # 1. Create Consumer Group (idempotent)
    try:
        # '$' means "only new messages from now on"
        # Use '0' to read all history
        r.xgroup_create(STREAM_KEY, GROUP_NAME, id='$', mkstream=True)
        print(f"Created consumer group '{GROUP_NAME}'")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"Consumer group '{GROUP_NAME}' already exists.")
        else:
            raise e

    print(f"Consumer '{CONSUMER_NAME}' starting...")

    while True:
        try:
            # 2. Read from Stream
            # > means "give me new messages for this group"
            entries = r.xreadgroup(GROUP_NAME, CONSUMER_NAME, {STREAM_KEY: '>'}, count=10, block=2000)
            
            if not entries:
                continue
                
            for stream, messages in entries:
                for message_id, message_data in messages:
                    # Parse the JSON payload
                    event_data = json.loads(message_data['data'])
                    
                    # --- PROCESSING LOGIC HERE ---
                    # In Phase 3, we will call the model here.
                    # For now, just print stats.
                    latency = time.time() - event_data['ingestion_time']
                    print(f"[{message_id}] {event_data['event_type']} by User {event_data['user_id']} (Latency: {latency:.4f}s)")
                    
                    # 3. Acknowledge message (mark as processed)
                    r.xack(STREAM_KEY, GROUP_NAME, message_id)
                    
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    run_consumer()
