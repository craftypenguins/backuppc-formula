# -*- coding: utf-8 -*-

import subprocess
import time

import re
import pytest
import testinfra

# Get the result keys from running the following in test container:
#   salt-call state.sls backuppc.xs.install  --out=json


# A fixture to push the 'states' tag definitions into each test
# instead of having to retype them every function
# todo - Some of these values will be different based on pillar
@pytest.fixture()
def states(host):
    states = {
        "service_state": "service_|-backuppc_service_|-backuppc_|-running",
        "systemd_state": ("file_|-backuppc_systemd_unit_|"
                          "-/lib/systemd/system/backuppc.service_|-managed"),
        "symlink_state": ("file_|-backuppc-cgi-image-symlink_|"
                          "-/srv/backuppc/cgi-bin/image_|-symlink")
    }
    return states


# A fixture 'cludge' to clean out container items so that the states
# that rely on 'onchanges' triggers get called properly.
# You will also need to make tests on states to make sure that they
# don't trigger when no on-change even has fired
@pytest.fixture()
def cleanout(host):
    # todo - Some of these need to come from the pillar
    host.run("deluser backuppc")
    host.run("rm -rf /tmp/BackupPC-*")
    host.run("rm -rf /etc/backuppc")
    host.run("systemctl disable backuppc.service")
    host.run("systemctl stop backuppc.service")
    host.run("rm -rf /lib/systemd/system/backuppc.service")


def test_salt_backuppc_systemd_state(host, states, cleanout):
    # Clean out so state fires downloads
    # todo - We need to get the backuppc name from the pillar

    systemd_state = states['systemd_state']
    symlink_state = states['symlink_state']

    result = host.salt("state.sls_id", ["backuppc_systemd_unit",
                                        "backuppc.server.service"])

    assert symlink_state in result, (
            "Systemd state did not require/onchanges the Install States")

    assert systemd_state in result
    assert result[systemd_state].get('result', False) is True

    changes = result[systemd_state].get('changes', False)
    assert isinstance(changes, dict)

    diff = changes.get('diff', False)
    assert diff, "No changes made for backuppc unit file"
    assert "New file" in diff, "BackupPC systemd unit file not new"


def test_salt_backuppc_service_state(host, states, cleanout):
    # Clean out so state fires downloads
    # todo - We need to get the backuppc name from the pillar

    systemd_state = states['systemd_state']
    symlink_state = states['symlink_state']
    service_state = states['service_state']

    result = host.salt("state.sls_id", ["backuppc_service",
                                        "backuppc.server.service"])

    assert systemd_state in result, (
            "Service state did not require/onchanges Systemd Unit State")
    assert symlink_state in result, (
            "Service state did not require/onchanges the Install States")

    assert service_state in result
    assert result[service_state].get('result', False) is True

    comment = result[service_state].get('comment', False)
    assert "already running" not in comment, ("BackupPC service was "
                                              "already running")

    assert "backuppc has been enabled, and is running" in comment, (
        "BackupPC service was not enabled or is not running")
