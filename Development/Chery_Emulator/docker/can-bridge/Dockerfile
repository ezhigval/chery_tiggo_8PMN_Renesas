# Dockerfile for CAN bridge service (Linux socketcan for macOS)
# This allows running socketcan on macOS through Docker

FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    iproute2 \
    can-utils \
    && rm -rf /var/lib/apt/lists/*

# Create vcan interface script
RUN echo '#!/bin/bash\n\
modprobe vcan\n\
ip link add dev vcan0 type vcan\n\
ip link set up vcan0\n\
echo "vcan0 interface created"\n\
' > /usr/local/bin/setup-vcan.sh && \
    chmod +x /usr/local/bin/setup-vcan.sh

# Copy CAN bridge script
WORKDIR /app
COPY core/can_bridge.py ./can_bridge.py

# Expose CAN bridge TCP port
EXPOSE 1238

# Start script
CMD ["/bin/bash", "-c", "/usr/local/bin/setup-vcan.sh && python3 can_bridge.py"]

