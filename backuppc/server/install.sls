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

#backuppc-binary-directory:
  #file.directory:
    #- name: {{ backuppc.lookup.binary_directory }}
    #- makedirs: True

#backuppc-data-directory:
  #file.directory:
    #- name: {{ backuppc.lookup.data_directory }}
    #- makedirs: True

#backuppc-data-directory:
  #file.directory:
    #- name: {{ backuppc.lookup.data_directory }}
    #- makedirs: True

backuppc_configure:
  cmd.run:
    - name: >
        perl configure.pl --batch --cgi-dir /srv/backuppc/cgi-bin
        --config-dir /etc/backuppc --log-dir /var/log/backuppc
        --data-dir /var/lib/backuppc --html-dir /srv/backuppc/image
        --html-dir-url /BackupPC --install-dir /usr/local/backuppc
    - cwd: /tmp/{{ backuppc_name }}
    - unless: test -f /etc/backuppc/config.pl
    - require:
        - user: backuppc
    - onchanges:
        - archive: backuppc_download

backuppc-cgi-image-symlink:
  file.symlink:
    - name: /srv/backuppc/cgi-bin/image
    - target: /srv/backuppc/image
    - require:
        - cmd: backuppc_configure
    - onchanges:
        - cmd: backuppc_configure


