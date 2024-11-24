import pandas as pd
from sklearn.ensemble import IsolationForest
from influxdb_client import InfluxDBClient, Point, WriteOptions
import matplotlib.pyplot as plt


def load_data(file_path):
    """Load and preprocess the data."""
    try:
        data = pd.read_csv(file_path)
        data['EdgeStartTimestamp'] = pd.to_datetime(data['EdgeStartTimestamp'])
        return data
    except Exception as e:
        raise ValueError(f"Error loading data: {e}")


def feature_engineering(data):
    """Create and aggregate features for anomaly detection."""
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


def block_ip_aws_waf(ip):
    """Simulate blocking IP in AWS WAF."""
    try:
        print(f"Simulating AWS WAF block for IP: {ip}")
    except Exception as e:
        print(f"Error blocking IP {ip}: {e}")


def visualize_anomalies(features):
    """Improved visualization of anomalies."""
    plt.figure(figsize=(12, 8))
    
    # Separate normal and anomalous data
    normal_data = features[features['Anomaly'] == 'Normal']
    anomalous_data = features[features['Anomaly'] == 'Anomaly']
    
    # Scatter plot for normal and anomalous points
    plt.scatter(normal_data['RequestCountByIP'], normal_data['AverageBytesByIP'], 
                c='blue', label='Normal', alpha=0.6)
    plt.scatter(anomalous_data['RequestCountByIP'], anomalous_data['AverageBytesByIP'], 
                c='red', label='Anomaly', alpha=0.8, edgecolor='black')
    
    # Logarithmic scale if needed
    plt.yscale('log')
    plt.xscale('log')
    
    # Adding labels, title, and legend
    plt.xlabel('Request Count by IP (Log Scale)', fontsize=12)
    plt.ylabel('Average Bytes by IP (Log Scale)', fontsize=12)
    plt.title('Enhanced Anomaly Detection in Network Traffic', fontsize=15)
    plt.legend(fontsize=12)
    
    # Annotate top anomalies for clarity
    top_anomalies = anomalous_data.nlargest(3, 'AverageBytesByIP')
    for _, row in top_anomalies.iterrows():
        plt.annotate(row['ClientIP'], (row['RequestCountByIP'], row['AverageBytesByIP']),
                     textcoords="offset points", xytext=(10, 10), ha='center', fontsize=10, color='black')
    
    # Save and show plot
    plt.savefig('enhanced_anomaly_visualization.png')
    plt.show()


def send_to_influxdb(anomalous_ips, influx_bucket, influx_org, influx_token, influx_url):
    """Send data to InfluxDB."""
    try:
        client = InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
        # Correctly initialize the write API
        write_api = client.write_api(write_options=WriteOptions(batch_size=1, flush_interval=10))

        for _, row in anomalous_ips.iterrows():
            point = Point("anomaly_detection") \
                .tag("ClientIP", row["ClientIP"]) \
                .field("ConfidenceScore", row["ConfidenceScore"]) \
                .field("RequestCountByIP", row["RequestCountByIP"]) \
                .field("AverageBytesByIP", row["AverageBytesByIP"]) \
                .field("Hour", row["Hour"]) \
                .field("Reason", row["Reason"]) \
                .time(pd.Timestamp.now().isoformat())
            write_api.write(bucket=influx_bucket, record=point)

        print("Data successfully written to InfluxDB.")
        client.close()
    except Exception as e:
        print(f"Error writing to InfluxDB: {e}")


# Main Execution
if __name__ == "__main__":
    # Load data
    data = load_data('test-dataset.csv')
    
    # Feature engineering
    features = feature_engineering(data)
    
    # Detect anomalies
    features = detect_anomalies(features)
    
    # Extract anomalies and calculate confidence scores
    anomalous_ips = features[features['Anomaly'] == 'Anomaly'].copy()
    anomalous_ips['ConfidenceScore'] = anomalous_ips.apply(
        lambda row: calculate_confidence_score(row, features), axis=1
    )
    anomalous_ips = assign_anomaly_reasons(anomalous_ips, features)
    
    # Apply blocking policy
    BLOCK_THRESHOLD = 70
    blocked_ips = anomalous_ips[anomalous_ips['ConfidenceScore'] >= BLOCK_THRESHOLD]
    
    # Simulate blocking in AWS WAF
    for ip in blocked_ips['ClientIP']:
        block_ip_aws_waf(ip)
    
    # Send data to InfluxDB
    influx_bucket = "network_monitoring"
    influx_org = "DataAnalysis"
    influx_token = "mASZ6S1GGvomci8iPeD9r8SSnRncxWhlNIagiZT39Ei--Xmc_V-1RCmo409VtUOABqDLw4LgCobuDJlNiSf6Kw=="
    influx_url = "http://localhost:8086"
    send_to_influxdb(anomalous_ips, influx_bucket, influx_org, influx_token, influx_url)
    
    # Save results
    features.to_csv('features_with_anomalies.csv', index=False)
    anomalous_ips.to_csv('anomalous_ips_with_scores.csv', index=False)
    blocked_ips.to_csv('blocked_ips.csv', index=False)
    
    # Visualize results
    visualize_anomalies(features)
    
    print("Anomaly detection completed. Results saved to CSV files.")
