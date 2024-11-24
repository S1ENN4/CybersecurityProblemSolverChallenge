import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest

# Ensure logs and graphs folders exist
LOGS_FOLDER = 'logs'
GRAPHS_FOLDER = 'graphs'
os.makedirs(LOGS_FOLDER, exist_ok=True)
os.makedirs(GRAPHS_FOLDER, exist_ok=True)

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

def visualize_anomalies(features):
    """Visualize anomalies."""
    plt.figure(figsize=(12, 8))
    normal_data = features[features['Anomaly'] == 'Normal']
    anomalous_data = features[features['Anomaly'] == 'Anomaly']

    # Scatter plot for normal and anomalous points
    plt.scatter(normal_data['RequestCountByIP'], normal_data['AverageBytesByIP'], 
                c='blue', label='Normal', alpha=0.6)
    plt.scatter(anomalous_data['RequestCountByIP'], anomalous_data['AverageBytesByIP'], 
                c='red', label='Anomaly', alpha=0.8, edgecolor='black')
    plt.yscale('log')
    plt.xscale('log')
    plt.xlabel('Request Count by IP (Log Scale)', fontsize=12)
    plt.ylabel('Average Bytes by IP (Log Scale)', fontsize=12)
    plt.title('Anomaly Detection in Network Traffic', fontsize=15)
    plt.legend(fontsize=12)
    plt.savefig(os.path.join(GRAPHS_FOLDER, 'anomaly_visualization.png'))
    plt.show()

def plot_time_series(data):
    """Plot traffic volume over time."""
    traffic_over_time = data.groupby(data['EdgeStartTimestamp'].dt.hour)['ClientRequestBytes'].sum()
    plt.figure(figsize=(12, 6))
    traffic_over_time.plot(kind='line', marker='o', color='blue')
    plt.title('Traffic Volume Over Time (Hourly)', fontsize=15)
    plt.xlabel('Hour of Day', fontsize=12)
    plt.ylabel('Total Request Bytes', fontsize=12)
    plt.grid(True)
    plt.savefig(os.path.join(GRAPHS_FOLDER, 'traffic_volume_over_time.png'))
    plt.show()

def plot_top_ips(data, top_n=10):
    """Plot top N IPs by total data transfer."""
    top_ips = data.groupby('ClientIP')['ClientRequestBytes'].sum().nlargest(top_n)
    plt.figure(figsize=(12, 6))
    top_ips.plot(kind='bar', color='orange')
    plt.title(f'Top {top_n} IPs by Total Data Transfer', fontsize=15)
    plt.xlabel('Client IP', fontsize=12)
    plt.ylabel('Total Request Bytes', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True, axis='y')
    plt.savefig(os.path.join(GRAPHS_FOLDER, 'top_ips_by_data_transfer.png'))
    plt.show()

def plot_anomaly_reasons(anomalies):
    """Plot a pie chart of anomaly reasons."""
    reason_counts = anomalies['Reason'].value_counts()
    plt.figure(figsize=(8, 8))
    reason_counts.plot(kind='pie', autopct='%1.1f%%', startangle=140, colormap='viridis')
    plt.title('Breakdown of Anomaly Reasons', fontsize=15)
    plt.ylabel('')
    plt.savefig(os.path.join(GRAPHS_FOLDER, 'anomaly_reasons_breakdown.png'))
    plt.show()

def plot_anomaly_heatmap(anomalies):
    """Plot a heatmap of anomalies by hour."""
    anomalies['Hour'] = anomalies['Hour'].astype(int)
    heatmap_data = anomalies.groupby('Hour')['ClientIP'].count().reset_index()
    heatmap_data = heatmap_data.pivot_table(index='Hour', values='ClientIP', aggfunc='sum')
    plt.figure(figsize=(10, 8))
    sns.heatmap(heatmap_data, cmap='coolwarm', annot=True, fmt='g')
    plt.title('Hourly Anomalies Heatmap', fontsize=15)
    plt.xlabel('Hour of Day', fontsize=12)
    plt.ylabel('Frequency of Anomalies', fontsize=12)
    plt.savefig(os.path.join(GRAPHS_FOLDER, 'hourly_anomaly_heatmap.png'))
    plt.show()

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
    
    # Save results in logs folder
    features.to_csv(os.path.join(LOGS_FOLDER, 'features_with_anomalies.csv'), index=False)
    anomalous_ips.to_csv(os.path.join(LOGS_FOLDER, 'anomalous_ips_with_scores.csv'), index=False)
    
    # Visualize results
    visualize_anomalies(features)
    plot_time_series(data)
    plot_top_ips(data)
    plot_anomaly_reasons(anomalous_ips)
    plot_anomaly_heatmap(anomalous_ips)

    print(f"Anomaly detection completed. Results saved to the '{LOGS_FOLDER}' and visualizations to the '{GRAPHS_FOLDER}' folder.")
