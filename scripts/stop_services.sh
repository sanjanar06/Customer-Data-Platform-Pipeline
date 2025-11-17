set -e

echo "=========================================="
echo "Stopping CDP Docker Services"
echo "=========================================="

cd docker

docker-compose down

echo "==========Services Stopped!=============="
echo "To remove volumes: docker-compose down -v"
echo "To start again: ./scripts/start_services.sh"