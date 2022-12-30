# global test config

import json
import subprocess
import time
from pathlib import Path
from shutil import copytree, rmtree
from tempfile import TemporaryDirectory

import pytest

LOCAL_CHAMBER = "chamber"
CLOUD_CHAMBER = "cloud-chamber"
TEST_SERVICE = "credentials_helper_system_test"

CLEANUP_TIMEOUT = 5

TEST_ENVIRONMENT = {
    "DOCKER_CREDENTIALS_SERVICE": TEST_SERVICE,
    "DOCKER_CREDENTIALS_DEBUG": "1",
    "DOCKER_CREDENTIALS_LOGLEVEL": "DEBUG",
    "DOCKER_CREDENTIALS_LOGFILE": "stderr",
}


@pytest.fixture
def local_chamber():
    return LOCAL_CHAMBER


@pytest.fixture
def cloud_chamber():
    return CLOUD_CHAMBER


@pytest.fixture
def service():
    return TEST_SERVICE


def _get_services(chamber):
    output = subprocess.check_output([chamber, "list-services"]).decode()
    services = output.strip().split("\n")
    return services


@pytest.fixture(autouse=True)
def test_environment(monkeypatch):
    for k, v in TEST_ENVIRONMENT.items():
        monkeypatch.setenv(k, v)
    yield True


def _delete_service(chamber, service):
    if service in _get_services(chamber):
        data = subprocess.check_output([chamber, "export", service]).decode()
        if data:
            for key in json.loads(data).keys():
                subprocess.check_call([chamber, "delete", service, key])
                timeout = time.time() + CLEANUP_TIMEOUT
                while service in _get_services(chamber):
                    assert time.time() < timeout
                assert service not in _get_services(chamber)


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    try:
        for chamber in LOCAL_CHAMBER, CLOUD_CHAMBER:
            _delete_service(chamber, TEST_SERVICE)
        yield True
    finally:
        for chamber in LOCAL_CHAMBER, CLOUD_CHAMBER:
            _delete_service(chamber, TEST_SERVICE)


@pytest.fixture(scope="session", autouse=True)
def preserve_dotpath():
    dotpath = Path.home() / ".docker"
    save_dotpath = dotpath.is_dir()
    with TemporaryDirectory() as tempdir:
        backup_dotpath = Path(tempdir) / "backup"
        if save_dotpath:
            copytree(dotpath, backup_dotpath)
            rmtree(dotpath)
        dotpath.mkdir()
        try:
            yield dotpath
        finally:
            rmtree(dotpath)
            if save_dotpath:
                copytree(backup_dotpath, dotpath)
