# -*- coding: utf-8 -*-
# vim: ft=sls
include:
  - backuppc.server.install

{%- from "backuppc/map.jinja" import backuppc with context %}

{% set backuppc_name = "BackupPC-" + backuppc.lookup.version -%}
{% set backuppc_archive_name = backuppc_name + ".tar.gz" -%}
{% set backuppc_package_url = backuppc.lookup.url ~ "/" ~ backuppc.lookup.version ~ "/" ~ backuppc_archive_name -%}
{% set backuppc_systemd_service_name = backuppc.lookup.systemd_name -%}
{% set backuppc_systemd_service_filepath = backuppc.lookup.systemd_path ~ "/" ~ backuppc_systemd_service_name -%}

backuppc_systemd_unit:
  file.managed:
    - name: {{ backuppc_systemd_service_filepath }}
    - source: salt://backuppc/templates/backuppc.service.jinja
    - template: jinja
    - require:
        - sls: backuppc.server.install

backuppc_service:
  service.running:
    - name: backuppc
    - enable: True
    - reload: True
    - watch:
        - file: backuppc_systemd_unit
    - require:
        - sls: backuppc.server.install

