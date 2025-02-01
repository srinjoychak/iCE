#!/bin/bash

# Function to check if specific containers are running
check_containers_running() {
  local required_containers=("ice_ui_container" "ice_backend_container" "ice_db_container")

  # Add the appropriate ollama container to the list if MODE is Offline
  if [ "$MODE" = "Offline" ]; then
    required_containers+=("$ollama_container")
  fi

  # Check if all required containers are running
  for container in "${required_containers[@]}"; do
    if ! docker ps --filter "name=$container" --filter "status=running" --format "{{.Names}}" | grep -q "^$container$"; then
      return 1
    fi
  done
  return 0
}

# Get the current IP address
ip_address=$(hostname -I | awk '{print $1}')

# Load environment variables from .env file
. ./.env

# Update /etc/hosts with the current IP address for iceservice.com
new_entry="$ip_address iceservice.com"
sudo sed -i '/iceservice.com/d' /etc/hosts
echo "$new_entry" | sudo tee -a /etc/hosts

# Replace placeholder IP address in docker-compose file
compose_file="docker-compose.yml"
sed -i "s/<ip_address>/$ip_address/g" "$compose_file"

# Remove existing containers
docker rm -f ice_ollama_gpu_container ice_ollama_cpu_container ice_db_container ice_backend_container ice_ui_container

# Remove existing images if needed
docker rmi ice_ui:latest ice_backend:latest ollama/ollama:latest mongo:latest

# Start stage 1, stage 2, and mongodb containers
docker-compose build --no-cache ice_ui ice_backend ice_db && docker-compose up -d ice_ui ice_backend ice_db

# Check if MODE is Offline
if [ "$MODE" = "Offline" ]; then
  # Determine which ollama service and container to start based on DEVICE_TYPE
  if [ "$DEVICE_TYPE" = "cpu" ]; then
    ollama_service="ice_ollama_cpu"
    ollama_container="ice_ollama_cpu_container"
  elif [ "$DEVICE_TYPE" = "cuda" ]; then
    ollama_service="ice_ollama_gpu"
    ollama_container="ice_ollama_gpu_container"
  else
    echo "Unknown DEVICE_TYPE: $DEVICE_TYPE. Please specify 'cpu' or 'cuda'."
    exit 1
  fi

  # Start the appropriate ollama service
  docker-compose up --build -d "$ollama_service"

  echo "Waiting for containers to initialize..."
  sleep 30

  # Use expect to interact with ollama
  expect << EOF
    spawn docker exec -it "$ollama_container" ollama run $OLLAMA_MODEL
    expect ">>> Send a message (/? for help)"
    send "/bye\r"
    expect eof
EOF
fi

# Check if all required containers are running
if check_containers_running; then
  echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
  echo "~                                        ~"
  printf "~  %-38s ~\n" "Access the service at:"
  printf "~  %-38s ~\n" "http://$ip_address:5006"
  echo "~                                        ~"
  echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
else
  echo "One or more containers are not running. Please check the Docker logs."
fi 