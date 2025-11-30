#!/bin/bash
# Simple script to start CAN bridge on macOS using Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Starting CAN Bridge for macOS ==="
echo ""
echo "This will:"
echo "  1. Build Docker image with Linux + socketcan"
echo "  2. Create vcan0 interface inside container"
echo "  3. Start CAN bridge service (TCP -> socketcan)"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Build and start
docker-compose up -d --build

echo ""
echo "✅ CAN bridge started!"
echo ""
echo "To check status:"
echo "  docker logs chery-can-bridge"
echo ""
echo "To stop:"
echo "  docker-compose down"
echo ""
echo "vcan0 interface is now available for QEMU (via host network)"

