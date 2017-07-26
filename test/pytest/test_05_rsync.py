# -*- coding: utf-8 -*-

import subprocess
import time

import re
import pytest
import testinfra

# Get the result keys from running the following in test container:
#   salt-call state.sls backuppc.rsync-bpc.install  --out=json

def test_salt_backuppc_rsync_state(host):
    # These are the state result dictionary keys
    download_state = "archive_|-rsync_download_|-/tmp_|-extracted"
    configure_state = "cmd_|-rsync_build_configure_|-./configure_|-run"
    make_state = "cmd_|-rsync_build_make_|-make_|-run"
    install_state = "cmd_|-rsync_build_install_|-make install_|-run"

    # The cleanup state string below is for a regex match
    # because the actual state key is based on the version, not static

    cleanup_state = "-rsync_build_cleanup_"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls", "backuppc.rsync-bpc.install")

    assert download_state in result
    assert result[download_state].get('result', False) is True
    assert configure_state in result
    assert result[configure_state].get('result', False) is True
    assert make_state in result
    assert result[make_state].get('result', False) is True
    assert install_state in result
    assert result[install_state].get('result', False) is True
    cleanup_dict = [result[key] for key in result.keys()
                    if re.search(cleanup_state, key)][0]
    assert cleanup_dict
    assert cleanup_dict.get('result', False) is True

def test_salt_backuppc_rsync_installed(host):
    assert host.run(
        "ls /usr/local/bin/rsync_bpc"
        ).rc == 0
