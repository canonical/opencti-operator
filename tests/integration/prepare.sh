#!/bin/bash

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Spread suite prepare script, run after concierge has provisioned LXD and MicroK8s.

# The root-installed tox points to a Python managed by root's uv, which the ubuntu user that
# runs the tests cannot execute on Ubuntu 22.04 runners, so install tox for that user.
runuser -l ubuntu -c "uv tool install --python 3.12 tox --with tox-uv --quiet"
sudo ln -sf /home/ubuntu/.local/bin/tox /usr/local/bin/tox

# Docker on the runner sets the FORWARD policy to DROP, which blocks LXD container traffic.
sudo iptables -I DOCKER-USER -j ACCEPT

# https://charmhub.io/opensearch/docs/t-set-up#set-parameters-on-the-host-machine
sudo tee -a /etc/sysctl.conf > /dev/null <<EOT
vm.max_map_count=262144
vm.swappiness=0
net.ipv4.tcp_retries2=5
fs.file-max=1048576
EOT

sudo sysctl -p

sudo microk8s kubectl apply -f - << EOF
apiVersion: v1
kind: Service
metadata:
  name: nginx-ingress-microk8s-controller
  namespace: ingress
spec:
  selector:
    name: nginx-ingress-microk8s
  ports:
    - name: http
      port: 80
      targetPort: 80
    - name: https
      port: 443
      targetPort: 443
EOF
