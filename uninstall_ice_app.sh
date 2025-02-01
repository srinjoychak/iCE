#!/bin/bash
echo "Removing the containers"
docker rm -f ice_ollama_gpu_container ice_ollama_cpu_container ice_db_container ice_backend_container ice_ui_container

echo "Deleting the docker images"
docker rmi ice_ui:latest ice_backend:latest ollama/ollama:latest mongo:latest

#echo "Deleting the database Volume"
#sudo rm -rf ~/ice_db_dump

echo "The application uninstalled successfully"  