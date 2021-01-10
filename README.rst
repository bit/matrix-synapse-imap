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
          enabled: true
          create_users: true
          server: "mail.example.com"
          plain_userid: true
          append_domain: "some.domain.com"

The ``create_users``-key specifies whether to create Matrix accounts
for valid system accounts.

The ``server``-key specifies the name of the imap server, it must support SSL connections.

The ``plain_userid``-key forces the unaltered userid to be send to the imap server

The ``append_domain``-key overrides or appends email domain
