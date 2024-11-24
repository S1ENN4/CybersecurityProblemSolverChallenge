import time
import random
import json
import pandas as pd
from confluent_kafka import Producer
from faker import Faker

# Initialize Faker instance and Kafka producer
fake = Faker()

producer = Producer({
    'bootstrap.servers': 'localhost:9093',  # Ensure you use the correct port
})

# Load data from the CSV file
data = pd.read_csv('test-dataset.csv')  # or use the absolute path

# Generate logs based on CSV rows
def generate_log(row):
    return {
        'ClientIP': row['ClientIP'],  # Use the real ClientIP from CSV
        'ClientRequestBytes': random.randint(500, 5000),  # Generate random request bytes
        'EdgeStartTimestamp': pd.Timestamp.now().isoformat(),  # Current timestamp
        'ClientRequestMethod': fake.http_method(),  # Generate a fake HTTP method
        'ClientRequestURI': row['ClientRequestURI'],  # Use the real URI from CSV
        'ClientRequestHost': row['ClientRequestHost'],  # Use the real host
        'ClientRequestReferer': fake.url(),  # Generate a fake referer
        'ClientRequestScheme': row['ClientRequestScheme'],  # Use the real scheme from CSV
        'ClientRequestUserAgent': fake.user_agent()  # Generate a fake user agent
    }

# Callback function to confirm delivery
def on_delivery(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

# Send logs to Kafka
for _, row in data.iterrows():
    # Generate a random number of requests for each ClientIP
    num_requests = random.randint(1, 10)
    for _ in range(num_requests):
        log = generate_log(row)
        producer.produce('raw_network_data', key=str(row['ClientIP']), value=json.dumps(log), callback=on_delivery)
        print(f"Sent log: {log}")
        producer.flush()  # Ensure the message is sent
        time.sleep(0.2)  # Reduce delay to simulate higher traffic
