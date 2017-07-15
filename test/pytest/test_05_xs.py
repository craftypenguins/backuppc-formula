# -*- coding: utf-8 -*-

import subprocess
import time

import re
import pytest
import testinfra

# Get the result keys from running the following in test container:
#   salt-call state.sls backuppc.xs.install  --out=json

def test_salt_backuppc_xs_state(host):
    # These are the state result dictionary keys
    download_state = "archive_|-xs_download_|-/tmp_|-extracted"
    perl_state = "cmd_|-xs_build_perl_|-perl Makefile.PL_|-run"
    make_state = "cmd_|-xs_build_make_|-make_|-run"
    install_state = "cmd_|-xs_build_install_|-make install_|-run"

    # The cleanup state string below is for a regex match
    # because the actual state key is based on the version, not static

    cleanup_state = "-xs_build_cleanup_"

    # Note: You could run stat.sls_id to only run one ID from sls
    result = host.salt("state.sls", "backuppc.xs.install")

    assert download_state in result
    assert result[download_state].get('result', False) is True
    assert perl_state in result
    assert result[perl_state].get('result', False) is True
    assert make_state in result
    assert result[make_state].get('result', False) is True
    assert install_state in result
    assert result[install_state].get('result', False) is True
    cleanup_dict = [result[key] for key in result.keys()
                    if re.search(cleanup_state, key)][0]
    assert cleanup_dict
    assert cleanup_dict.get('result', False) is True

def test_salt_backuppc_xs_installed(host):
    assert host.run(
        "ls /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC/XS.pm"
        ).rc == 0
