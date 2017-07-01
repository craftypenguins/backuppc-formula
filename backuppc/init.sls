# vim: ft=sls
# Init backuppc
{%- from "backuppc/map.jinja" import backuppc with context %}
{# Below is an example of having a toggle for the state #}

{% if backuppc.server.enabled %}
include:
  - backuppc.server.install
  - backuppc.server.config
  - backuppc.server.service
{% else %}
'backuppc.server disabled':
  test.succeed_without_changes
{% endif %}

