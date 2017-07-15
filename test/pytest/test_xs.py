# -*- coding: utf-8 -*-

import subprocess
import time

import pytest
import testinfra
import re


def test_passwd_file(host):
    passwd = host.file("/etc/passwd")
    assert passwd.contains("root")
    assert passwd.user == "root"
    assert passwd.group == "root"
    assert passwd.mode == 0o644

def test_pillars(host):
    pillar = host.salt("pillar.items")
    expected = {
        'version': '1.2.3',
    }
    assert pillar == {
        'backuppc': {'lookup': expected}
    }

def test_salt_backuppc_xs_git(host):
    download_state = "archive_|-xs_download_|-/tmp_|-extracted"
    perl_state = "cmd_|-xs_build_perl_|-perl Makefile.PL_|-run"
    make_state = "cmd_|-xs_build_make_|-make_|-run"
    install_state = "cmd_|-xs_build_install_|-make install_|-run"
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
