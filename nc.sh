#!/bin/bash

# This script is used to test the connection between the server and client.
# It uses the netcat command to send a message to the server.
# To run the script, execute the following command: ./nc.sh <server> <port> <message>

server=${1:-server}
port=${2:-12345}
message=${3:-"Hello server :D"}

# Create a network to connect the client to the server inside the container
docker network create testing_net > /dev/null 2>&1

docker run --rm --network="tp0_testing_net" bash:latest bash -c "echo $message | nc -v $server $port"

docker network rm testing_net > /dev/null 2>&1
