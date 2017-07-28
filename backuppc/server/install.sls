# -*- coding: utf-8 -*-
# vim: ft=sls

{%- from "backuppc/map.jinja" import backuppc with context %}

{% set backuppc_name = "BackupPC-" + backuppc.lookup.version -%}
{% set backuppc_archive_name = backuppc_name + ".tar.gz" -%}
{% set backuppc_package_url = backuppc.lookup.url ~ "/" ~ backuppc.lookup.version ~ "/" ~ backuppc_archive_name -%}

backuppc_user:
  user.present:
    - name: backuppc
    - fullname: "BackupPC user account"
    - home: "/var/lib/backuppc"
    - system: true
  
backuppc_file_listing_dep:
  pkg.installed:
    - name: libfile-listing-perl

backuppc_cgi_dep:
  pkg.installed:
    - name: libcgi-pm-perl

backuppc_download:
  archive.extracted:
    - name: /tmp
    - source: {{ backuppc_package_url }}
    - source_hash: {{ backuppc.lookup.hash }}
    - require:
        - pkg: backuppc_file_listing_dep
        - pkg: backuppc_cgi_dep

backuppc_configure:
  cmd.run:
    - name: perl configure.pl
    - cwd: /tmp/{{ backuppc_name }}
    - unless: test -f /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC/XS.pm
    - require:
        - pkg: build-essential
        - user: backuppc
    - onchanges:
        - archive: backuppc_download

backuppc-directory:
  file.directory:
    - name: {{ backuppc.lookup.binary_directory }}
    - makedirs: True

backuppc-data-directory:
  file.directory:
    - name: {{ backuppc.lookup.data_directory }}
    - makedirs: True


