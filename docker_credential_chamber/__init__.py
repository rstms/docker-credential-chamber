"""
docker_credential_chamber

  An implementation of a credential helper for 'docker login'
  using `chamber` for the backend storage

 reference:
 https://docs.docker.com/engine/reference/commandline/login/#credential-helpers

"""

from .cli import cli
from .version import __version__

__all__ = ["cli", "__version__"]
