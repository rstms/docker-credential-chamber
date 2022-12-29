# cli test cases

import json
import re
from logging import info

import pytest
from click.testing import CliRunner

import docker_credential_chamber
from docker_credential_chamber import cli


@pytest.fixture
def run():
    runner = CliRunner()

    def _run(cmd, **kwargs):
        expected_exit = kwargs.pop("expected_input", 0)
        kwargs["catch_exceptions"] = False
        result = runner.invoke(cli, cmd, **kwargs)
        assert result.exit_code == expected_exit, result.output
        return result.output

    return _run


def test_cli_version():
    """Test reading version and module name"""
    assert docker_credential_chamber.__name__ == "docker_credential_chamber"
    version = docker_credential_chamber.__version__
    assert version
    assert isinstance(version, str)
    parts = version.split(".")
    assert len(parts) == 3
    for part in parts:
        assert part.isnumeric()
    info(f"version is {version}")


def test_cli_help(run):
    """Test CLI help."""
    output = run(["--help"])
    assert re.search(
        r"^[\s]*--help[\s]*Show this message and exit.[\s]*$",
        output,
        flags=re.MULTILINE,
    ), output


def test_cli_install(run):
    output = run(["install"])
    assert isinstance(output, str)
    assert output == ""


def test_cli_erase(run):
    output = run(["erase"])
    assert isinstance(output, str)
    assert output == ""


def test_cli_get(run):
    output = run(["get"])
    assert isinstance(output, str)
    data = json.loads(output)
    assert data is None


def test_cli_list(run):
    output = run(["list"])
    assert isinstance(output, str)
    data = json.loads(output)
    assert isinstance(data, dict)


def test_cli_store(run, shared_datadir):
    testfile = shared_datadir / "creds.json"
    assert testfile.is_file()
    test_str = testfile.read_text()
    test_data = json.loads(test_str)
    assert isinstance(test_data, dict)
    output = run(["store"], input=testfile.open("r"))
    assert isinstance(output, str)
    assert output == ""
