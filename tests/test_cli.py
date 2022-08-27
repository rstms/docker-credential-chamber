
import re

from click.testing import CliRunner

import docker_credential_chamber
from docker_credential_chamber import cli


def test_cli_version():
    """Test reading version and module name"""
    assert docker_credential_chamber.__name__ == "docker_credential_chamber"
    version = docker_credential_chamber.__version__
    assert version
    assert isinstance(version, str)
    parts = version.split('.')
    assert len(parts) == 3
    for part in parts:
        assert part.isnumeric()


def test_cli_help():
    """Test CLI help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result.output
    assert re.search(
        r"^[\s]*--help[\s]*Show this message and exit.[\s]*$",
        result.output,
        flags=re.MULTILINE,
    ), result.output
