#!/bin/bash

# Start Kafka services
echo "Starting Kafka services..."
docker-compose up -d

# Wait for Kafka to be ready
echo "Waiting for Kafka to initialize..."
sleep 20  # Adjust this as needed

# Start Log Generator
echo "Starting log generator..."
python faker_log_generator.py &

# Start Anomaly Detection
echo "Starting anomaly detection..."
python anomaly_detection.py
