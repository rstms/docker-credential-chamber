# global test config

import json
import os
import subprocess
from pathlib import Path
from shutil import copytree, rmtree
from tempfile import TemporaryDirectory

import pytest

LOCAL_CHAMBER = "chamber"
CLOUD_CHAMBER = "cloud-chamber"
TEST_SERVICE_ENV = "DOCKER_CREDENTIALS_SERVICE"
TEST_SERVICE = "credentials_helper_system_test"


@pytest.fixture
def local_chamber():
    return LOCAL_CHAMBER


@pytest.fixture
def cloud_chamber():
    return CLOUD_CHAMBER


@pytest.fixture
def service():
    return TEST_SERVICE


@pytest.fixture(scope="session", autouse=True)
def global_environment():
    try:
        os.environ[TEST_SERVICE_ENV] = TEST_SERVICE
        yield True
    finally:
        os.environ.pop(TEST_SERVICE_ENV, True)

        def get_services():
            output = subprocess.check_output(
                [chamber, "list-services"]
            ).decode()
            services = output.strip().split("\n")
            return services

        for chamber in LOCAL_CHAMBER, CLOUD_CHAMBER:
            services = get_services()
            if TEST_SERVICE in services:
                data = subprocess.check_output(
                    [chamber, "export", TEST_SERVICE]
                ).decode()
                if data:
                    for key in json.loads(data).keys():
                        subprocess.check_call(
                            [chamber, "delete", TEST_SERVICE, key]
                        )
            services = get_services()
            assert TEST_SERVICE not in services


@pytest.fixture()
def docker_dotpath():
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
