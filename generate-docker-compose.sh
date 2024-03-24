#!/bin/bash

TOTAL_CLIENTS=$1

# Creates the docker-compose.yml file
cat > docker-compose-dev.yaml <<EOF
version: '3.9'
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    volumes:
      - ./config/server_config.ini:/config.ini
      - ./config/bets.csv:/bets.csv
    networks:
      - testing_net
EOF

# Append the configuration for the clients
for (( i=1; i<=TOTAL_CLIENTS; i++ ))
do
cat >> docker-compose-dev.yaml <<EOF

  client$i:
    container_name: client$i
    image: client:latest
    entrypoint: python3 /main.py
    environment:
      - CLI_ID=$i
      - CLI_LOG_LEVEL=DEBUG
    volumes:
      - ./config/client_config.ini:/config.ini
      - ./.data/agency-$i.csv:/bets.csv
    networks:
      - testing_net
    depends_on:
      - server
EOF
done

# Finally append the network configuration
cat >> docker-compose-dev.yaml <<EOF

networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOF

echo "docker-compose.yml file created successfully with $TOTAL_CLIENTS clients."