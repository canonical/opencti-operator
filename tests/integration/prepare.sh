#!/bin/bash

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Pre-run script for integration test operator-workflows action.
# https://github.com/canonical/operator-workflows/blob/main/.github/workflows/integration_test.yaml

# OpenSearch/RabbitMQ charms are deployed on lxd and OpenCTI charm is deployed on microk8s.

TESTING_MODEL="$(juju switch)"

# lxd should be install and init by a previous step in integration test action.
echo "bootstrapping lxd juju controller"
# Change microk8s default file limits
echo "ulimit -n 458752" | sudo tee -a /var/snap/microk8s/current/args/containerd-env
sudo snap restart microk8s
sg snap_microk8s -c "microk8s status --wait-ready"
sg snap_microk8s -c "juju bootstrap localhost localhost"

echo "Switching to testing model"
sg snap_microk8s -c "juju switch $TESTING_MODEL"

[[ -n "${CI}" ]] && [[ -n "${GITHUB_RUN_ID}" ]] && sudo rm -rf \
  /usr/local/lib/node_modules/ \
  /usr/local/.ghcup \
  /usr/local/julia1.11.1 \
  /usr/local/share/powershell \
  /usr/local/share/chromium \
  /usr/local/share/vcpkg \
  /opt/hostedtoolcache
