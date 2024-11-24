import pandas as pd
import os
import json
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
from confluent_kafka import Consumer, KafkaException, KafkaError

# Ensure logs folder exists
LOGS_FOLDER = 'logs'
os.makedirs(LOGS_FOLDER, exist_ok=True)

def kafka_consumer_to_dataframe(consumer, batch_size=10):
    """Consume Kafka messages in batches and convert them to a Pandas DataFrame."""
    messages = []
    for _ in range(batch_size):
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                raise KafkaException(msg.error())
        messages.append(json.loads(msg.value().decode('utf-8')))
    if not messages:
        return None
    return pd.DataFrame(messages)

def feature_engineering(data):
    """Create and aggregate features for anomaly detection."""
    data['ClientRequestBytes'] = pd.to_numeric(data['ClientRequestBytes'], errors='coerce')
    data['EdgeStartTimestamp'] = pd.to_datetime(data['EdgeStartTimestamp'], errors='coerce')

    data['RequestCountByIP'] = data.groupby('ClientIP')['ClientIP'].transform('count')
    data['AverageBytesByIP'] = data.groupby('ClientIP')['ClientRequestBytes'].transform('mean')
    data['Hour'] = data['EdgeStartTimestamp'].dt.hour

    features = data.groupby('ClientIP').agg({
        'RequestCountByIP': 'max',
        'AverageBytesByIP': 'max',
        'Hour': 'mean'
    }).reset_index()
    return features

def detect_anomalies(features, contamination=0.05):
    """Train the Isolation Forest model and predict anomalies."""
    model = IsolationForest(contamination=contamination, random_state=42)
    feature_columns = ['RequestCountByIP', 'AverageBytesByIP', 'Hour']
    features['Anomaly'] = model.fit_predict(features[feature_columns])
    features['Anomaly'] = features['Anomaly'].map({1: 'Normal', -1: 'Anomaly'})
    return features

def calculate_confidence_score(row, features):
    """Calculate the confidence score for anomalies."""
    score = 0
    if row['RequestCountByIP'] > features['RequestCountByIP'].quantile(0.95):
        score += 40
    if row['AverageBytesByIP'] > features['AverageBytesByIP'].quantile(0.95):
        score += 30
    if row['Hour'] < 6 or row['Hour'] > 22:
        score += 20
    return min(score, 100)

def assign_anomaly_reasons(anomalous_ips, features):
    """Assign reasons for each detected anomaly."""
    reasons_list = []
    for _, row in anomalous_ips.iterrows():
        reasons = []
        if row['RequestCountByIP'] > features['RequestCountByIP'].quantile(0.95):
            reasons.append("Unusually high request count.")
        if row['AverageBytesByIP'] > features['AverageBytesByIP'].quantile(0.95):
            reasons.append("High data transfer per request.")
        if row['Hour'] < 6 or row['Hour'] > 22:
            reasons.append("Unusual activity outside normal business hours.")
        reasons_list.append("; ".join(reasons) if reasons else "No clear reason identified.")
    anomalous_ips['Reason'] = reasons_list
    return anomalous_ips

def append_to_csv(data, file_name):
    """Append data to a CSV file."""
    full_path = os.path.join(LOGS_FOLDER, file_name)  # Save to logs folder
    header = not os.path.exists(full_path)  # Add header if file doesn't exist
    data.to_csv(full_path, mode='a', index=False, header=header)

if __name__ == '__main__':
    # Kafka configuration
    kafka_topic = 'raw_network_data'
    kafka_bootstrap_servers = 'localhost:9093'
    kafka_group_id = 'anomaly_detection_group'

    consumer = Consumer({
        'bootstrap.servers': kafka_bootstrap_servers,
        'group.id': kafka_group_id,
        'auto.offset.reset': 'earliest'
    })

    consumer.subscribe([kafka_topic])

    try:
        print("Starting continuous log processing. Press Ctrl+C to stop.")
        while True:
            # Consume logs in batches
            raw_data = kafka_consumer_to_dataframe(consumer, batch_size=10)
            if raw_data is None:
                continue

            print(f"Processing {len(raw_data)} messages...")

            # Feature engineering
            features = feature_engineering(raw_data)

            # Detect anomalies
            features = detect_anomalies(features)

            # Add confidence scores
            features['ConfidenceScore'] = features.apply(
                lambda row: calculate_confidence_score(row, features), axis=1
            )

            # Save all logs
            append_to_csv(features, 'all_logs.csv')

            # Extract anomalies
            anomalies = features[features['Anomaly'] == 'Anomaly'].copy()
            anomalies = assign_anomaly_reasons(anomalies, features)
            append_to_csv(anomalies, 'anomalies.csv')

            # Block IPs with high confidence scores
            BLOCK_THRESHOLD = 70
            blocked_ips = anomalies[anomalies['ConfidenceScore'] >= BLOCK_THRESHOLD]
            append_to_csv(blocked_ips, 'blocked_ips.csv')

            print(f"Processed batch: {len(raw_data)} messages. Results saved in the 'logs' folder.")

    except KeyboardInterrupt:
        print("Stopping log processing.")
    finally:
        consumer.close()
