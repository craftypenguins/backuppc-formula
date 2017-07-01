# -*- coding: utf-8 -*-
# vim: ft=sls

{%- from "backuppc/map.jinja" import backuppc with context %}

build-essential:
  pkg.installed

xs_build_checkout:
  git.detached:
    - name: {{ backuppc.lookup.xs_repo }}
    - ref: {{ backuppc.lookup.xs_version }}
    - target: /tmp/backuppc_xs

xs_build_perl:
  cmd.run:
    - name: perl Makefile.PL
    - cwd: /tmp/backuppc_xs
    - unless: test -f /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC/XS.pm
    - require:
        - git: xs_build_checkout
        - pkg: build-essential

xs_build_make:
  cmd.run:
    - name: make
    - cwd: /tmp/backuppc_xs
    - unless: test -f /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC/XS.pm
    - require:
        - cmd: xs_build_perl

xs_build_install:
  cmd.run:
    - name: make install
    - cwd: /tmp/backuppc_xs
    - unless: test -f /usr/local/lib/x86_64-linux-gnu/perl/*/BackupPC/XS.pm
    - require:
        - cmd: xs_build_make



