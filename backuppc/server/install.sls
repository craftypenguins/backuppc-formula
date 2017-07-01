# -*- coding: utf-8 -*-
# vim: ft=sls

{%- from "backuppc/map.jinja" import backuppc with context %}

{% set backuppc_name = "BackupPC-" + backuppc.lookup.version -%}
{% set backuppc_archive_name = backuppc_name + ".tar.gz" -%}
{% set backuppc_package_url = "https://github.com/backuppc/backuppc/releases/download/" ~ backuppc.lookup.version ~ "/" ~ backuppc_archive_name -%}

backuppc-directory:
  file.directory:
    - name: {{ backuppc.look.binary_directory }}
    - makedirs: True

backuppc-data-directory:
  file.directory:
    - name: {{ backuppc.lookup.data_directory }}
    - makedirs: True

backuppc-download:
  archive.extracted:
    - name: /tmp/backuppc
    - source: {{ backuppc_package_url }}
    - user: backuppc
    - group: backuppc
    - if_missing: /etc/backuppc
