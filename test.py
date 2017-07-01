# -*- coding: utf-8 -*-

import subprocess
import time

import pytest
import testinfra


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
    run_label = ("git_|-xs_build_checkout_|-"
            "https://github.com/backuppc/backuppc-xs.git_|-detached")
    result = host.salt("state.sls", "backuppc.xs.install")
    assert run_label in result
    assert result[run_label].get('result',False) is True

def test_salt_backuppc_xs_installed(host):
    assert host.run(
        "ls /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC/XS.pm"
        ).rc == 0
