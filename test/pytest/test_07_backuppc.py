# -*- coding: utf-8 -*-

import subprocess
import time

import re
import pytest
import testinfra

# Get the result keys from running the following in test container:
#   salt-call state.sls backuppc.xs.install  --out=json

def test_salt_backuppc_state(host):
    # These are the state result dictionary keys
    config_directory_state = "file_|-backuppc-directory_|-None_|-directory"
    data_directory_state =
        "file_|-backuppc-data-directory_|-/var/lib/backuppc_|-directory"
    libcgi_state = "pkg_|-backuppc_cgi_dep_|-libcgi-pm-perl_|-installed"
    libfile_state = "pkg_|-backuppc_file_listing_dep_|-libfile-listing-perl_|-installed"
    archive_state = "archive_|-backuppc_download_|-/tmp_|-extracted"
    configure_state = "archive_|-backuppc_download_|-/tmp_|-extracted"
    user_state = "user_|-backuppc_user_|-backuppc_|-present"
    install_state = "cmd_|-xs_build_install_|-make install_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls", "backuppc.install")

    assert config_directory_state in result
    assert result[config_directory_state].get('result', False) is True
    assert data_directory_state in result
    assert result[data_directory_state].get('result', False) is True
    assert libcgi_state in result
    assert result[libcgi_state].get('result', False) is True
    assert libfile_state in result
    assert result[libfile_state].get('result', False) is True
    assert archive_state in result
    assert result[archive_state].get('result', False) is True
    assert configure_state in result
    assert result[configure_state].get('result', False) is True
    assert configure_state in result
    assert result[configure_state].get('result', False) is True
    assert install_state in result
    assert result[install_state].get('result', False) is True

def test_salt_backuppc_installed(host):
    assert host.run(
        "ls /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC/XS.pm"
        ).rc == 0
