
# Cybersecurity Problem Solver Challenge

## Introduction
First and foremost, I would like to express my gratitude for the opportunity to join this team. Working on this project has been an exciting challenge that kept me engaged even beyond the initial analysis. After completing the required tasks, I decided to take the project a step further by implementing a more robust solution. As a result, the work is divided into two segments: Part 1, which addresses the original requirements of the challenge, and Part 2, which focuses on scalability and future-proofing, as detailed in this README.

This project is a cybersecurity challenge aimed at detecting and analyzing anomalies in network traffic data. Its objective is to leverage machine learning and data visualization techniques to identify potential security risks, propose mitigation strategies, and communicate findings effectively through clear visualizations and comprehensive documentation.

---

## Objective

The main objectives of the project include:

1. **Data Analysis**: Extract insights from network traffic logs to identify patterns, anomalies, and potential security threats.
2. **Anomaly Detection**: Use machine learning models to detect unusual behaviors in network traffic.
3. **Visualization**: Create visual tools for better understanding traffic patterns and anomalies.
4. **Automation**: Build a robust pipeline to process network logs and generate insights dynamically.
5. **Mitigation**: Simulate security policies to mitigate risks, such as blocking malicious IPs.
6. **Scalability**:

---

## Requirements

1. **Python Environment**:
   - Python 3.8 or higher
   - Required libraries listed in `requirements.txt`
   
2. **Files and Folders**:
   - `test-dataset.csv`: Contains the network traffic data.
   - `anomaly_detection.py`: Main script for anomaly detection and visualization.
   - Folders:
     - `logs/`: Contains generated CSV files for anomalies and blocked IPs.
     - `graphs/`: Contains generated visualizations.

3. **Libraries**:
   - Pandas
   - Matplotlib
   - Seaborn
   - Scikit-learn
   - OS (standard Python library)

---

## Key Features

### 1. **Anomaly Detection**
- **Machine Learning**: Uses `IsolationForest` from Scikit-learn to detect anomalies.
- **Features**:
  - Request count per IP.
  - Average bytes transferred per IP.
  - Hour of activity.

### 2. **Visualization**
- **Graphs**:
  - Anomaly Scatter Plot: Highlights anomalous traffic.
  - Traffic Volume Time Series: Shows hourly traffic volume.
  - Top IPs by Data Transfer: Identifies IPs transferring the most data.
  - Anomaly Reasons Pie Chart: Summarizes causes of anomalies.
  - Heatmap: Shows hourly anomaly distribution.

### 3. **Dynamic Log Processing**
- Logs and results are saved dynamically:
  - Detected anomalies in `logs/anomalous_ips_with_scores.csv`.
  - Blocked IPs in `logs/blocked_ips.csv`.
  - Full traffic analysis in `logs/features_with_anomalies.csv`.

---q

## Usage

### 1. Clone the Repository
```bash
git clone https://github.com/YourRepo/CybersecurityProblemSolverChallenge.git
cd CybersecurityProblemSolverChallenge
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Anomaly Detection Script
```bash
python anomaly_detection.py
```

---

## Outputs

### Logs (`logs/`)
1. `features_with_anomalies.csv`: Full dataset with anomaly labels.
2. `anomalous_ips_with_scores.csv`: Details of detected anomalies, including confidence scores and reasons.
3. `blocked_ips.csv`: List of IPs blocked due to high confidence of malicious behavior.

### Graphs (`graphs/`)
1. **Anomaly Scatter Plot**: Visualizes normal and anomalous traffic.
2. **Traffic Volume Time Series**: Displays hourly traffic activity.
3. **Top IPs by Data Transfer**: Highlights heavy data transfer IPs.
4. **Anomaly Reasons Pie Chart**: Explains anomaly causes.
5. **Hourly Anomaly Heatmap**: Shows anomalies' hourly distribution.

---

## Insights Gained

1. **Traffic Patterns**:
   - The hourly time series plot reveals peak traffic times and quiet periods.
   
2. **Anomaly Detection**:
   - The scatter plot clearly separates anomalous data points from normal traffic.
   - Top anomaly reasons include unusual request counts and high data transfers during off-hours.

3. **Mitigation**:
   - High-confidence anomalies were flagged and added to a blocking policy, simulating an AWS WAF rule for IP blocking.
