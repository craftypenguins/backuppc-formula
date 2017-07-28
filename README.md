=====
backuppc
=====

Install backuppc server or client setup

.. note::


    See the full `Salt Formulas installation and usage instructions
    <http://docs.saltstack.com/en/latest/topics/development/conventions/formulas.html>`_.

Available states
================

.. contents::
    :local:

``backuppc.server``
------------

``backuppc.server.install``
--------------------

Installs the backuppc server from release tarball

``backuppc.server.config``
-------------------

Manages the backuppc server configuration.

``backuppc.server.service``
--------------------

Manages the startup and running state of the backuppc.

``backuppc.server.client_config``
--------------------------

Manages client configurations on the server.  Should pull down mine data to setup backup.

