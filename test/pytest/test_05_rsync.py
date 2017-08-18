# -*- coding: utf-8 -*-

import subprocess
import time

import re
import pytest
import testinfra

# Get the result keys from running the following in test container:
#   salt-call --out=json state.sls_id <STATE_ID> backuppc.rsync-bpc.install


# Test that we have a clean build to work with
def test_salt_backuppc_rsync_clean(host):
    assert not host.file("/usr/local/bin/rsync_bpc").exists, (
        "Running test on instance with old artifacts",
        "Might not be accurate")


# Test that the archive can be downloaded
def test_salt_backuppc_rsync_download_state(host):
    # Clean out so archive downloads
    host.run("rm -rf /tmp/rsync-bpc*")
    host.run("rm -rf /usr/local/bin/rsync_bpc")

    # These are the state result dictionary keys
    download_state = "archive_|-rsync_download_|-/tmp_|-extracted"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["rsync_download",
                                        "backuppc.rsync-bpc.install"])

    assert download_state in result
    assert result[download_state].get('result', False) is True

    changes = result[download_state].get('changes', False)
    assert isinstance(changes, dict)

    extracted_files = changes.get('extracted_files', False)
    assert isinstance(extracted_files, list), "No files extracted"


# Test that the download doesn't run on already exiting
def test_salt_backuppc_rsync_download_exists_state(host):
    # These are the state result dictionary keys
    download_state = "archive_|-rsync_download_|-/tmp_|-extracted"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["rsync_download",
                                        "backuppc.rsync-bpc.install"])

    assert download_state in result
    assert result[download_state].get('result', False) is True

    comment = result[download_state].get('comment', False)
    assert "already present" in comment


# Test the configure state no action
def test_salt_backuppc_rsync_configure_onchanges(host):
    # These are the state result dictionary keys
    download_state = "archive_|-rsync_download_|-/tmp_|-extracted"
    configure_state = "cmd_|-rsync_build_configure_|-./configure_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["rsync_build_configure",
                                        "backuppc.rsync-bpc.install"])

    assert download_state in result, (
            "Configure State did not require/onchanges the Download State")

    assert configure_state in result, (
            "Configure State not present in run")

    assert result[configure_state].get('result', False) is True

    comment = result[configure_state].get('comment', False)
    assert "onchanges" in comment


# Test the configure state
def test_salt_backuppc_rsync_configure_state(host):
    # Clean out so onchanges fires
    host.run("rm -rf /tmp/rsync-bpc*")

    # These are the state result dictionary keys
    download_state = "archive_|-rsync_download_|-/tmp_|-extracted"
    pkg_state = "pkg_|-build-essential_|-build-essential_|-installed"
    configure_state = "cmd_|-rsync_build_configure_|-./configure_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["rsync_build_configure",
                                        "backuppc.rsync-bpc.install"])

    assert download_state in result, (
            "Configure State did not require/onchanges the Download State")

    assert pkg_state in result, (
            "Configure State did not require Build Essentials pkg")

    assert configure_state in result, (
            "Configure State not present in run")

    assert result[configure_state].get('result', False) is True

    changes = result[configure_state].get('changes', False)
    assert isinstance(changes, dict)

    configure_output = changes.get('stdout', False)
    assert "configuration successful" in configure_output, (
            "./configure output did not report success")


# Test the configure state no action
def test_salt_backuppc_rsync_make_onchanges(host):
    # These are the state result dictionary keys
    make_state = "cmd_|-rsync_build_make_|-make_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["rsync_build_make",
                                        "backuppc.rsync-bpc.install"])

    comment = result[make_state].get('comment', False)
    assert "onchanges" in comment


# Test the make state
def test_salt_backuppc_rsync_make_state(host):
    # Clean out so onchanges fires
    host.run("rm -rf /tmp/rsync-bpc*")

    # These are the state result dictionary keys
    download_state = "archive_|-rsync_download_|-/tmp_|-extracted"
    configure_state = "cmd_|-rsync_build_configure_|-./configure_|-run"
    pkg_state = "pkg_|-build-essential_|-build-essential_|-installed"
    make_state = "cmd_|-rsync_build_make_|-make_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["rsync_build_make",
                                        "backuppc.rsync-bpc.install"])

    assert download_state in result, (
            "Make State did not require Download State")

    assert configure_state in result, (
            "Make State did not require/onchagnes the Configure State")

    assert pkg_state in result, (
            "Make State did not require Build Essentials pkg")

    assert make_state in result, (
            "Make State not present in run")

    assert result[make_state].get('result', False) is True

    changes = result[make_state].get('changes', False)
    assert isinstance(changes, dict)

    make_retcode = changes.get('retcode', False)
    assert make_retcode == 0


# Test the install state no action
def test_salt_backuppc_rsync_install_onchanges(host):
    # These are the state result dictionary keys
    install_state = "cmd_|-rsync_build_install_|-make install_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["rsync_build_install",
                                        "backuppc.rsync-bpc.install"])

    comment = result[install_state].get('comment', False)
    assert "onchanges" in comment


# Test the install state
def test_salt_backuppc_rsync_install_state(host):
    # Clean out so onchanges fires
    host.run("rm -rf /tmp/rsync-bpc*")

    # These are the state result dictionary keys
    download_state = "archive_|-rsync_download_|-/tmp_|-extracted"
    configure_state = "cmd_|-rsync_build_configure_|-./configure_|-run"
    make_state = "cmd_|-rsync_build_make_|-make_|-run"
    pkg_state = "pkg_|-build-essential_|-build-essential_|-installed"
    install_state = "cmd_|-rsync_build_install_|-make install_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["rsync_build_install",
                                        "backuppc.rsync-bpc.install"])

    assert download_state in result, (
            "Install State did not require Download State")

    assert configure_state in result, (
            "Install State did not require/onchanes the Configure State")

    assert make_state in result, (
            "Install State did not require/onchanes the Make State")

    assert pkg_state in result, (
            "Install State did not require Build Essentials pkg")

    assert install_state in result
    assert result[install_state].get('result', False) is True

    changes = result[install_state].get('changes', False)
    assert isinstance(changes, dict)

    retcode = changes.get('retcode')
    assert retcode == 0

    assert host.file("/usr/local/bin/rsync_bpc")


# Test the cleanup state not needed if not triggered
def test_salt_backuppc_rsync_cleanup_state_onchanges(host):

    cleanup_state = "-rsync_build_cleanup_"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["rsync_build_cleanup",
                                        "backuppc.rsync-bpc.install"])

    cleanup_dict = [result[key] for key in result.keys()
                    if re.search(cleanup_state, key)][0]
    assert cleanup_dict
    comment = cleanup_dict.get('comment', False)
    assert "onchanges" in comment


# Test the cleanup state
def test_salt_backuppc_rsync_cleanup_state(host):
    # Clean out so onchanges fires
    host.run("rm -rf /tmp/rsync-bpc*")
    host.run("rm -rf /usr/local/bin/rsync_bpc")

    # These are the state result dictionary keys
    download_state = "archive_|-rsync_download_|-/tmp_|-extracted"
    configure_state = "cmd_|-rsync_build_configure_|-./configure_|-run"
    make_state = "cmd_|-rsync_build_make_|-make_|-run"
    install_state = "cmd_|-rsync_build_install_|-make install_|-run"

    # The cleanup state string below is for a regex match
    # because the actual state key is based on the version, not static

    cleanup_state = "-rsync_build_cleanup_"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["rsync_build_cleanup",
                                        "backuppc.rsync-bpc.install"])

    assert download_state in result, (
            "Cleanup State did not require Download State")

    assert configure_state in result, (
            "Cleanup State did not require/onchanes the Configure State")

    assert make_state in result, (
            "Cleanup State did not require/onchanes the Make State")

    assert install_state in result, (
            "Cleanup State did not require/onchanes the Install State")

    cleanup_dict = [result[key] for key in result.keys()
                    if re.search(cleanup_state, key)][0]
    assert cleanup_dict
    assert cleanup_dict.get('result', False) is True

    changes = cleanup_dict.get('changes', False)
    assert isinstance(changes, dict)

    removed_files = changes.get('removed')
    assert removed_files, "Nothing removed"
