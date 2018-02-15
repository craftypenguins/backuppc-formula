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
        "xs_state": "cmd_|-xs_build_install_|-make install_|-run",
        "download_state": "archive_|-backuppc_download_|-/tmp_|-extracted",
        "configure_state": "-backuppc_configure_",  # Careful for regex
        "user_state": "user_|-backuppc_user_|-backuppc_|-present",
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


def test_salt_backuppc_user_state_clean(host, states):

    user_state = states['user_state']

    result = host.salt("state.sls_id", ["backuppc_user",
                                        "backuppc.server.install"])

    assert user_state in result

    comment = result[user_state].get('comment', False)
    assert "is present and up" not in comment, (
        "Running test on instance with old artifacts",
        "Tests might not be accurate")

# Example of using a parametrized test fixture
# This handling was generic enough that I used parm fixture
# to run through a list of simple package states
# Note - When used, it looks like tests after the first come
# out of order / random with respect to others in this test module
@pytest.mark.parametrize("state, state_id, package", [
    ('backuppc.server.install', 'backuppc_file_listing_dep', 'libfile-listing-perl'),
    ('backuppc.server.install', 'backuppc_cgi_dep', 'libcgi-pm-perl')])
def test_package_states(host, state, state_id, package):
    # Clean out so state fires downloads
    # todo - We need to get the package name from the pillar
    host.run("apt-get purge -y {}".format(package))

    state_tag = "pkg_|-{}_|-{}_|-installed".format(state_id, package)

    result = host.salt("state.sls_id", [state_id, state])

    assert state_tag in result
    assert result[state_tag].get('result', False) is True

    changes = result[state_tag].get('changes', False)
    assert isinstance(changes, dict)

    install_pkg = changes.get(package, False)
    assert install_pkg, "Package {} not installed".format(package)


def test_salt_backuppc_user_state(host, states, cleanout):
    # Clean out so state fires downloads
    # todo - We need to get the backuppc name from the pillar

    user_state = states['user_state']

    result = host.salt("state.sls_id", ["backuppc_user",
                                        "backuppc.server.install"])

    assert user_state in result
    assert result[user_state].get('result', False) is True

    changes = result[user_state].get('changes', False)
    assert isinstance(changes, dict)

    # Todo make this test based on pillar data for actual
    # home directory.  Make a salt call to get pillar data, and extract.
    home = changes.get('home', False)
    assert home == "/var/lib/backuppc", "BackupPC user home invalid"

    user = changes.get('name', False)
    assert user == "backuppc", "BackupPC user invalid"


# Test that user state run a second time makes no changes
def test_salt_backuppc_user_state_exists(host, states):

    user_state = states['user_state']

    result = host.salt("state.sls_id", ["backuppc_user",
                                        "backuppc.server.install"])

    assert user_state in result

    comment = result[user_state].get('comment', False)
    assert "is present and up" in comment
    changes = result[user_state].get('changes', False)
    assert isinstance(changes, dict)
    assert len(changes) == 0


# Test that the archive can be downloaded
def test_salt_backuppc_download_state(host, states):

    download_state = states['download_state']
    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["backuppc_download",
                                        "backuppc.server.install"])

    assert download_state in result
    assert result[download_state].get('result', False) is True

    changes = result[download_state].get('changes', False)
    assert isinstance(changes, dict)

    extracted_files = changes.get('extracted_files', False)
    assert isinstance(extracted_files, list), "No files extracted"


# Test that the download doesn't run on already exiting
def test_salt_backuppc_download_exists_state(host, states):

    download_state = states['download_state']

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["backuppc_download",
                                        "backuppc.server.install"])

    assert download_state in result
    assert result[download_state].get('result', False) is True

    comment = result[download_state].get('comment', False)
    assert "already present" in comment


# Test the build state no action
def test_salt_backuppc_configure_onchanges(host, states):

    configure_state = states['configure_state']

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["backuppc_configure",
                                        "backuppc.server.install"])

    configure_state_results = [result[key] for key in result.keys()
                               if re.search(configure_state, key)][0]
    assert configure_state_results

    comment = configure_state_results.get('comment', False)
    assert "onchanges" in comment


# Test the build configure state
def test_salt_backuppc_configure_state(host, cleanout, states):

    download_state = states['download_state']
    configure_state = states['configure_state']
    user_state = states['user_state']
    xs_state = states['xs_state']

    # These are the state result dictionary keys
    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["backuppc_configure",
                                        "backuppc.server.install"])

    assert download_state in result, (
            "Configure State did not require/onchanges the Download State")
    assert user_state in result, (
            "Configure State did not require the User State")
    assert xs_state in result, (
            "Configure State did not require the XS Library states")
    configure_state_results = [result[key] for key in result.keys()
                               if re.search(configure_state, key)][0]
    assert configure_state_results
    assert configure_state_results.get('result', False) is True

    changes = configure_state_results.get('changes', False)
    assert isinstance(changes, dict)

    assert 'stdout' in changes
    stdoutput = changes.get('stdout', False)
    assert "we are finished" in stdoutput, (
        "Makefile generation failed")


# Test the build make state
def test_salt_backuppc_symlink_state(host, cleanout, states):

    download_state = states['download_state']
    configure_state = states['configure_state']
    user_state = states['user_state']
    xs_state = states['xs_state']
    symlink_state = states['symlink_state']

    # These are the state result dictionary keys
    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["backuppc-cgi-image-symlink",
                                        "backuppc.server.install"])

    assert download_state in result, (
            "Symlink State did not require/onchanges the Download State")
    assert user_state in result, (
            "Symlink State did not require the User State")
    assert xs_state in result, (
            "Symlink State did not require the XS Library states")
    assert [result[key] for key in result.keys()
            if re.search(configure_state, key)][0], (
                "Symlink State did not require the Configure state"
            )
    assert symlink_state in result
    assert result[symlink_state].get('result', False) is True


# Test the symlink state no action
def test_salt_backuppc_symlink_onchanges(host, states):

    symlink_state = states['symlink_state']

    # Note: You could run state.sls_id to only run one ID from sls
    result = host.salt("state.sls_id", ["backuppc-cgi-image-symlink",
                                        "backuppc.server.install"])

    assert symlink_state in result
    assert result[symlink_state].get('result', False) is True

    comment = result[symlink_state].get('comment', False)
    assert "none of the onchanges" in comment


# def test_salt_backuppc_state(host):
    # # These are the state result dictionary keys
    # config_directory_state = "file_|-backuppc-directory_|-None_|-directory"
    # data_directory_state = ("file_|-backuppc-data-directory_|"
                            # "-/var/lib/backuppc_|-directory")
    # libcgi_state = "pkg_|-backuppc_cgi_dep_|-libcgi-pm-perl_|-installed"
    # libfile_state = ("pkg_|-backuppc_file_listing_dep_|"
                     # "-libfile-listing-perl_|-installed")
    # archive_state = "archive_|-backuppc_download_|-/tmp_|-extracted"
    # configure_state = "archive_|-backuppc_download_|-/tmp_|-extracted"
    # user_state = "user_|-backuppc_user_|-backuppc_|-present"
    # install_state = "cmd_|-xs_build_install_|-make install_|-run"

    # # Note: You could run state.sls_id to only run one ID from sls
    # result = host.salt("state.sls", "backuppc.server.install")

    # assert config_directory_state in result
    # assert result[config_directory_state].get('result', False) is True
    # assert data_directory_state in result
    # assert result[data_directory_state].get('result', False) is True
    # assert libcgi_state in result
    # assert result[libcgi_state].get('result', False) is True
    # assert libfile_state in result
    # assert result[libfile_state].get('result', False) is True
    # assert archive_state in result
    # assert result[archive_state].get('result', False) is True
    # assert configure_state in result
    # assert result[configure_state].get('result', False) is True
    # assert configure_state in result
    # assert result[configure_state].get('result', False) is True
    # assert user_state_state in result
    # assert result[user_state].get('result', False) is True
    # assert install_state in result
    # assert result[install_state].get('result', False) is True

# def test_salt_backuppc_installed(host):
    # assert host.run(
        # "ls /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC/XS.pm"
        # ).rc == 0
