# -*- coding: utf-8 -*-
# vim: ft=sls

{%- from "backuppc/map.jinja" import backuppc with context %}
{% set xs_build_name = "BackupPC-XS-" ~ backuppc.lookup.xs_version -%}
{% set xs_build_archive_name = xs_build_name + ".tar.gz" -%}
{% set xs_build_package_url = backuppc.lookup.xs_url ~ "/" ~ backuppc.lookup.xs_version ~ "/" ~ xs_build_archive_name -%}

build-essential:
  pkg.installed

xs_download:
  archive.extracted:
    - name: /tmp
    - source: {{ xs_build_package_url }}
    - source_hash: {{ backuppc.lookup.xs_hash }}
    - unless: perl -MBackupPC::XS -e 1

xs_build_perl:
  cmd.run:
    - name: perl Makefile.PL
    - cwd: /tmp/{{ xs_build_name }}
    - unless: test -f /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC/XS.pm
    - require:
        - pkg: build-essential
    - onchanges:
        - archive: xs_download

xs_build_make:
  cmd.run:
    - name: make
    - cwd: /tmp/{{ xs_build_name }}
    - onchanges:
        - cmd: xs_build_perl

xs_build_install:
  cmd.run:
    - name: make install
    - cwd: /tmp/{{ xs_build_name }}
    - onchanges:
        - cmd: xs_build_make

xs_build_cleanup:
  file.absent:
    - name: /tmp/{{ xs_build_name }}
    - unless: test ! -d /tmp/{{ xs_build_name }}
    - onchanges:
        - cmd: xs_build_install


