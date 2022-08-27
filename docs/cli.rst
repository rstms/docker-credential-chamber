Command Line Interface
======================

.. toctree::
   :maxdepth: 4

docker_credential_chamber CLI 
------------------------------

Non-default options may be configured using the environment variables shown in the help output.
The `install` command is used to configure docker to use the helper.
All other commands are used by the helper protocol.

.. click:: docker_credential_chamber.cli:cli
  :prog: docker-credential-chamber
  :nested: full
