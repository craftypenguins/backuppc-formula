# -*- coding: utf-8 -*-
# vim: ft=sls

{%- from "backuppc/map.jinja" import backuppc with context %}
{% set rsync_bpc_name = "rsync-bpc-" + backuppc.lookup.rsync_version -%}
{% set rsync_bpc_archive_name = rsync_bpc_name + ".tar.gz" -%}
{% set rsync_bpc_package_url = backuppc.lookup.rsync_url ~ "/" ~ backuppc.lookup.rsync_version ~ "/" ~ rsync_bpc_archive_name -%}

build-essential:
  pkg.installed

rsync_download:
  archive.extracted:
    - name: /tmp
    - source: {{ rsync_bpc_package_url }}
    - source_hash: {{ backuppc.lookup.rsync_hash }}
    - if_missing: /usr/local/bin/rsync_bpc

rsync_build_configure:
  cmd.run:
    - name: ./configure
    - cwd: /tmp/{{ rsync_bpc_name }}
    - onchanges:
        - archive: rsync_download
    - require:
        - pkg: build-essential

rsync_build_make:
  cmd.run:
    - name: make
    - cwd: /tmp/{{ rsync_bpc_name }}
    - onchanges:
        - cmd: rsync_build_configure
    - require:
        - pkg: build-essential

rsync_build_install:
  cmd.run:
    - name: make install
    - cwd: /tmp/{{ rsync_bpc_name }}
    - onchanges:
        - cmd: rsync_build_make
    - require:
        - pkg: build-essential

rsync_build_cleanup:
  file.absent:
    - name: /tmp/{{ rsync_bpc_name }}
    - unless: test ! -d /tmp/{{ rsync_bpc_name }}
    - onchanges:
        - cmd: rsync_build_install

