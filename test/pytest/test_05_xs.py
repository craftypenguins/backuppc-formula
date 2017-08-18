# -*- coding: utf-8 -*-

import subprocess
import time

import re
import pytest
import testinfra

# Get the result keys from running the following in test container:
#   salt-call state.sls backuppc.xs.install  --out=json


# Test that we have a clean build to work with
def test_salt_backuppc_xs_clean(host):
    assert host.run(
        "perl -MBackupPC::XS -e 1"
            ).rc > 0, (
        "Running test on instance with old artifacts",
        "..or Perl is not already on the system",
        "Tests might not be accurate")


# Test that the archive can be downloaded
def test_salt_backuppc_xs_download_state(host):
    # Clean out so archive downloads
    host.run("rm -rf /tmp/BackupPC-XS-*")
    host.run("rm -rf /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC")

    # These are the state result dictionary keys
    download_state = "archive_|-xs_download_|-/tmp_|-extracted"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["xs_download",
                                        "backuppc.xs.install"])

    assert download_state in result
    assert result[download_state].get('result', False) is True

    changes = result[download_state].get('changes', False)
    assert isinstance(changes, dict)

    extracted_files = changes.get('extracted_files', False)
    assert isinstance(extracted_files, list), "No files extracted"


# Test that the download doesn't run on already exiting
def test_salt_backuppc_xs_download_exists_state(host):
    # These are the state result dictionary keys
    download_state = "archive_|-xs_download_|-/tmp_|-extracted"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["xs_download",
                                        "backuppc.xs.install"])

    assert download_state in result
    assert result[download_state].get('result', False) is True

    comment = result[download_state].get('comment', False)
    assert "already present" in comment


# Test the build state no action
def test_salt_backuppc_xs_build_onchanges(host):
    # These are the state result dictionary keys
    download_state = "archive_|-xs_download_|-/tmp_|-extracted"
    build_state = "cmd_|-xs_build_perl_|-perl Makefile.PL_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["xs_build_perl",
                                        "backuppc.xs.install"])

    assert download_state in result, (
            "Build State did not require/onchanges the Download State")

    assert build_state in result, (
            "Build State not present in run")

    assert result[build_state].get('result', False) is True

    comment = result[build_state].get('comment', False)
    assert "onchanges" in comment


# Test the build state
def test_salt_backuppc_xs_build_state(host):
    # Clean out so onchanges fires
    host.run("rm -rf /tmp/BackupPC-XS-*")
    host.run("rm -rf /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC")

    # These are the state result dictionary keys
    download_state = "archive_|-xs_download_|-/tmp_|-extracted"
    pkg_state = "pkg_|-build-essential_|-build-essential_|-installed"
    build_state = "cmd_|-xs_build_perl_|-perl Makefile.PL_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["xs_build_perl",
                                        "backuppc.xs.install"])

    assert download_state in result, (
            "Build State did not require/onchanges the Download State")

    assert pkg_state in result, (
            "Build State did not require Build Essentials pkg")

    assert build_state in result, (
            "Build State not present in run")

    assert result[build_state].get('result', False) is True

    changes = result[build_state].get('changes', False)
    assert isinstance(changes, dict)

    stdoutput = changes.get('stdout', False)
    assert "Makefile for BackupPC::XS" in stdoutput, (
        "Makefile generation failed")


# Test the make state no action
def test_salt_backuppc_xs_make_onchanges(host):
    # These are the state result dictionary keys
    make_state = "cmd_|-xs_build_make_|-make_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["xs_build_make",
                                        "backuppc.xs.install"])

    comment = result[make_state].get('comment', False)
    assert "onchanges" in comment


# Test the make state
def test_salt_backuppc_xs_make_state(host):
    # Clean out so onchanges fires
    host.run("rm -rf /tmp/BackupPC-XS-*")

    # These are the state result dictionary keys
    download_state = "archive_|-xs_download_|-/tmp_|-extracted"
    pkg_state = "pkg_|-build-essential_|-build-essential_|-installed"
    build_state = "cmd_|-xs_build_perl_|-perl Makefile.PL_|-run"
    make_state = "cmd_|-xs_build_make_|-make_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["xs_build_make",
                                        "backuppc.xs.install"])

    assert download_state in result, (
            "Make State did not require Download State")

    assert build_state in result, (
            "Make State did not require/onchanges the Build State")

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
def test_salt_backuppc_xs_install_onchanges(host):
    # These are the state result dictionary keys
    install_state = "cmd_|-xs_build_install_|-make install_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["xs_build_install",
                                        "backuppc.xs.install"])

    comment = result[install_state].get('comment', False)
    assert "onchanges" in comment


# Test the install state
def test_salt_backuppc_xs_install_state(host):
    # Clean out so onchanges fires
    host.run("rm -rf /tmp/BackupPC-XS-*")
    host.run("rm -rf /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC")

    # These are the state result dictionary keys
    download_state = "archive_|-xs_download_|-/tmp_|-extracted"
    pkg_state = "pkg_|-build-essential_|-build-essential_|-installed"
    build_state = "cmd_|-xs_build_perl_|-perl Makefile.PL_|-run"
    make_state = "cmd_|-xs_build_make_|-make_|-run"
    install_state = "cmd_|-xs_build_install_|-make install_|-run"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["xs_build_install",
                                        "backuppc.xs.install"])

    assert download_state in result, (
            "Install State did not require Download State")

    assert pkg_state in result, (
            "Install State did not require Build Essentials pkg")

    assert build_state in result, (
            "Install State did not require/onchanes the Build State")

    assert make_state in result, (
            "Install State did not require/onchanes the Make State")

    assert install_state in result
    assert result[install_state].get('result', False) is True

    changes = result[install_state].get('changes', False)
    assert isinstance(changes, dict)

    retcode = changes.get('retcode')
    assert retcode == 0

    assert host.run(
        "perl -MBackupPC::XS -e 1"
            ).rc == 0, ("Module not installed")


# Test the cleanup state not needed if not triggered
def test_salt_backuppc_xs_cleanup_state_onchanges(host):

    cleanup_state = "-xs_build_cleanup_"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["xs_build_cleanup",
                                        "backuppc.xs.install"])

    cleanup_dict = [result[key] for key in result.keys()
                    if re.search(cleanup_state, key)][0]
    assert cleanup_dict
    comment = cleanup_dict.get('comment', False)
    assert "onchanges" in comment


# Test the cleanup state
def test_salt_backuppc_xs_cleanup_state(host):
    # Clean out so onchanges fires
    host.run("rm -rf /tmp/BackupPC-XS-*")
    host.run("rm -rf /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC")

    # These are the state result dictionary keys
    download_state = "archive_|-xs_download_|-/tmp_|-extracted"
    build_state = "cmd_|-xs_build_perl_|-perl Makefile.PL_|-run"
    make_state = "cmd_|-xs_build_make_|-make_|-run"
    install_state = "cmd_|-xs_build_install_|-make install_|-run"

    # The cleanup state string below is for a regex match
    # because the actual state key is based on the version, not static

    cleanup_state = "-xs_build_cleanup_"

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["xs_build_cleanup",
                                        "backuppc.xs.install"])

    assert download_state in result, (
            "Cleanup State did not require Download State")

    assert build_state in result, (
            "Cleanup State did not require/onchanes the Build State")

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
    assert removed_files
    # , "Nothing removed"

# def test_salt_backuppc_xs_state(host):
    # # These are the state result dictionary keys
    # download_state = "archive_|-xs_download_|-/tmp_|-extracted"
    # perl_state = "cmd_|-xs_build_perl_|-perl Makefile.PL_|-run"
    # make_state = "cmd_|-xs_build_make_|-make_|-run"
    # install_state = "cmd_|-xs_build_install_|-make install_|-run"

    # # The cleanup state string below is for a regex match
    # # because the actual state key is based on the version, not static

    # cleanup_state = "-xs_build_cleanup_"

    # # Note: You could run state.sls_id to only run one ID from sls
    # result = host.salt("state.sls", "backuppc.xs.install")

    # assert download_state in result
    # assert result[download_state].get('result', False) is True
    # assert perl_state in result
    # assert result[perl_state].get('result', False) is True
    # assert make_state in result
    # assert result[make_state].get('result', False) is True
    # assert install_state in result
    # assert result[install_state].get('result', False) is True
    # cleanup_dict = [result[key] for key in result.keys()
                    # if re.search(cleanup_state, key)][0]
    # assert cleanup_dict
    # assert cleanup_dict.get('result', False) is True


def test_salt_backuppc_xs_installed(host):
    assert host.run(
        "ls /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC/XS.pm"
        ).rc == 0
