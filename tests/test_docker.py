# cli test cases


import json
import logging
import os
import subprocess
from pathlib import Path
from tempfile import SpooledTemporaryFile

import pytest

info = logging.info
error = logging.error


@pytest.fixture
def run():
    def _run(cmd, **kwargs):
        kwargs["shell"] = True
        kwargs["capture_output"] = True
        kwargs["text"] = True
        info(cmd)
        ret = subprocess.run(cmd, **kwargs)
        if ret.stderr:
            error(ret.stderr)
        assert ret.returncode == 0, ret
        stdout = ret.stdout.strip()
        logging.info(stdout)
        return stdout

    return _run


@pytest.mark.parametrize("dialect", ["local", "cloud"])
def test_docker_login(
    run, docker_dotpath, service, local_chamber, cloud_chamber, dialect
):

    if dialect == "local":
        chamber = local_chamber
    elif dialect == "cloud":
        chamber = cloud_chamber
    else:
        assert False, f"Unexpected dialect: {dialect}"

    result = run("which docker-credential-chamber")
    test_bin = Path(result)
    assert test_bin.is_file()

    result = run(f"which {chamber}")
    chamber = Path(result)
    assert chamber.is_file()

    env = os.environ.copy()
    env["CHAMBER"] = str(chamber)
    env["DOCKER_CREDENTIALS_DEBUG"] = "1"
    env["DOCKER_CREDENTIALS_LOGLEVEL"] = "DEBUG"
    env["DOCKER_CREDENTIALS_LOGFILE"] = "dcc.log"

    assert "REGISTRY_NAME" in os.environ
    assert "REGISTRY_TOKEN" in os.environ

    run("docker-credential-chamber install", env=env)
    assert docker_dotpath.is_dir()
    docker_config = docker_dotpath / "config.json"
    assert docker_config.is_file()
    config = json.loads(docker_config.read_text())
    assert config == {"credsStore": "chamber"}

    ret = run("docker logout", env=env)
    info(ret)

    with SpooledTemporaryFile() as fp:
        fp.write(os.environ["REGISTRY_TOKEN"].encode())
        fp.seek(0)
        result = run(
            "docker login --username $REGISTRY_NAME --password-stdin",
            stdin=fp,
            env=env,
        )
    info(result)
    assert result == "Login Succeeded"

    ret = run("docker logout", env=env)
    info(ret)
