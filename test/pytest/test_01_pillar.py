# -*- coding: utf-8 -*-

import subprocess
import time

import pytest
import testinfra

def test_pillars(host):
    pillar = host.salt("pillar.items")
    expected = {
        'version': '1.2.3',
    }
    assert pillar == {
        'backuppc': {'lookup': expected}
    }

