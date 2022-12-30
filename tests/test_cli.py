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
    runner = CliRunner(mix_stderr=False)

    def _run(cmd, **kwargs):
        expected_exit = kwargs.pop("expected_exit", 0)
        kwargs["catch_exceptions"] = False
        result = runner.invoke(cli, cmd, **kwargs)
        assert result.exit_code == expected_exit, result.output
        return result.stdout, result.stderr

    return _run


@pytest.fixture
def store(run, shared_datadir):
    def _store(filename):
        testfile = shared_datadir / filename
        assert testfile.is_file()
        test_str = testfile.read_text()
        test_data = json.loads(test_str)
        assert isinstance(test_data, dict)
        return run(["store"], input=testfile.open("r"))

    return _store


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
    output, error = run(["--help"])
    assert re.search(
        r"^[\s]*--help[\s]*Show this message and exit.[\s]*$",
        output,
        flags=re.MULTILINE,
    ), output


def test_cli_install(run):
    output, error = run(["install"])
    assert isinstance(output, str)
    assert output == ""


def test_cli_store(store):
    output, error = store("creds.json")
    assert isinstance(output, str)
    assert output == ""


def test_cli_erase(store, run, shared_datadir):
    store("creds.json")
    server_file = shared_datadir / "server_url"
    output, error = run(["erase"], input=server_file.open("r"))
    assert isinstance(output, str)
    assert output == ""


def test_cli_get(store, run, shared_datadir):
    store("creds.json")
    server_file = shared_datadir / "server_url"
    output, error = run(["get"], input=server_file.open("r"))
    assert isinstance(output, str)
    data = json.loads(output)
    assert isinstance(data, dict)
    assert set(list(data.keys())) == set(["Username", "Secret"])


def test_cli_list(store, run):
    store("creds.json")
    output, error = run(["list"])
    assert isinstance(output, str)
    data = json.loads(output)
    assert isinstance(data, dict)
