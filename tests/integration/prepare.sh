#!/bin/bash

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Pre-run script for integration test operator-workflows action.
# https://github.com/canonical/operator-workflows/blob/main/.github/workflows/integration_test.yaml

# OpenSearch/RabbitMQ charms are deployed on lxd and OpenCTI charm is deployed on Canonical kubernetes.

TESTING_MODEL="$(juju switch)"

# lxd should be install and init by a previous step in integration test action.
echo "bootstrapping lxd juju controller"
juju bootstrap localhost localhost

echo "Switching to testing model"
juju switch $TESTING_MODEL

# https://charmhub.io/opensearch/docs/t-set-up#set-parameters-on-the-host-machine
sudo tee -a /etc/sysctl.conf > /dev/null <<EOT
vm.max_map_count=262144
vm.swappiness=0
net.ipv4.tcp_retries2=5
fs.file-max=1048576
EOT

sudo sysctl -p

[[ -n "${CI}" ]] && [[ -n "${GITHUB_RUN_ID}" ]] && sudo rm -rf \
  /usr/local/lib/node_modules/ \
  /usr/local/.ghcup \
  /usr/local/julia1.11.1 \
  /usr/local/share/powershell \
  /usr/local/share/chromium \
  /usr/local/share/vcpkg \
  /opt/hostedtoolcache
