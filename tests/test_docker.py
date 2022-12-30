# cli test cases


import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from tempfile import SpooledTemporaryFile

import pytest

logger = logging.getLogger(__name__)

info = logger.info
error = logger.error


@pytest.fixture
def run():
    def _run(cmd, **kwargs):
        if isinstance(cmd, str):
            kwargs["shell"] = True
        kwargs["capture_output"] = True
        kwargs["text"] = True
        info(cmd)
        ret = subprocess.run(cmd, **kwargs)
        info(f"[stdout] {ret.stdout}")
        info(f"[stderr] {ret.stderr}")
        assert ret.returncode == 0, ret
        return ret.stdout.strip()

    return _run


@pytest.mark.parametrize("dialect", ["cloud", "local"])
def test_docker_login(
    run, service, local_chamber, cloud_chamber, dialect, monkeypatch
):
    dotpath = Path.home() / ".docker"
    shutil.rmtree(dotpath)

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

    assert "REGISTRY_NAME" in os.environ
    assert "REGISTRY_TOKEN" in os.environ

    run("docker-credential-chamber install", env=env)
    assert dotpath.is_dir()
    docker_config = dotpath / "config.json"
    assert docker_config.is_file()
    config = json.loads(docker_config.read_text())
    assert "credsStore" in config
    assert config["credsStore"] == "chamber"

    ret = run("docker logout", env=env)
    info(ret)

    with SpooledTemporaryFile() as fp:
        fp.write(os.environ["REGISTRY_TOKEN"].encode())
        fp.seek(0)
        result = run(
            [
                "docker",
                "login",
                "--username",
                os.environ["REGISTRY_NAME"],
                "--password-stdin",
            ],
            stdin=fp,
            env=env,
        )
    info(result)
    assert result == "Login Succeeded"

    ret = run("docker logout", env=env)
    info(ret)
