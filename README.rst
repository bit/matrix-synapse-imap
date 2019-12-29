IMAP auth provider for Synapse
==============================

Allows Synapse to use IMAP to login users.

Installation
------------

pip3 install matrix-synapse-imap

Usage
-----

Example Synapse config:

.. code:: yaml

    password_providers:
      - module: "imap_auth_provider.IMAPAuthProvider"
        config:
          create_users: true
          server: "mail.example.com"

The ``create_users``-key specifies whether to create Matrix accounts
for valid system accounts.

The ``server``-key specifies the name of the imap server, it must support SSL connections.

