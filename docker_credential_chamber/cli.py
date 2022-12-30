#!/usr/bin/env python3

import json
import logging
import os
import sys
import time
from base64 import b32decode, b32encode
from pathlib import Path
from subprocess import CalledProcessError, check_call, check_output

import click

from .exception_handler import ExceptionHandler

ENABLE_LOGGING = False

READBACK_TIMEOUT = 5


def encode_server(server):
    key = b32encode(server.encode()).decode()
    key = key.replace("=", "_")
    key = key.lower()
    return key


def decode_key(key):
    key = key.replace("_", "=")
    server_url = b32decode(key.encode().upper()).decode()
    return server_url


class DCC:
    def __init__(
        self,
        service,
        vault_token=None,
        vault_addr=None,
        chamber=None,
        logger=None,
    ):
        self.service = service
        self.vault_token = vault_token
        self.vault_addr = vault_addr
        self.chamber = chamber or "chamber"
        if ENABLE_LOGGING:
            self.logger = logger
            self.debug(self._chamber_version())
        else:
            self.logger = None

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"{self.__class__.__name__}:{Path(self.chamber).stem}"

    def _chamber_version(self):
        try:
            version = check_output([self.chamber, "version"])
        except CalledProcessError:
            version = check_output([self.chamber, "--version"])
        return f"{self.chamber} {version}"

    def install(self):
        config_dir = Path.home() / ".docker"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.json"
        if config_file.is_file():
            config = json.loads(config_file.read_text())
        else:
            config = {}
        config["credsStore"] = "chamber"
        config_file.write_text(json.dumps(config))

    def info(self, msg, **kwargs):
        if self.logger:
            self.logger.info(f"{self}: {msg}", **kwargs)

    def debug(self, msg, **kwargs):
        if self.logger:
            self.logger.debug(f"{self}: {msg}", **kwargs)

    def error(self, msg, **kwargs):
        if self.logger:
            self.logger.error(f"{self}: {msg}", **kwargs)
        sys.stderr.write(f"docker-credential-chamber: {msg}\n")

    def _env(self):
        ret = os.environ.copy()
        if self.vault_token:
            ret["VAULT_TOKEN"] = self.vault_token
        if self.vault_addr:
            ret["VAULT_ADDR"] = self.vault_addr
        return ret

    def get(self, server):
        self.debug(f"get({server=})")
        secrets = self.read()
        ret = secrets.get(server, {})
        if not ret:
            self.server_not_found(server)
        self.debug(f"get() -> {ret}")
        return ret

    def put(self, server, username, secret):
        self.debug(f"put({server=} {username=} {secret=})")
        current = self.read()
        update = current.copy()
        update[server] = {"Username": username, "Secret": secret}
        self.write(update, current)

    def list(self):
        self.debug("list()")
        secrets = self.read()
        ret = {k: v["Username"] for k, v in secrets.items()}
        self.debug(f"list() -> {ret}")
        return ret

    def delete(self, server):
        self.debug(f"delete({server=})")
        current = self.read()
        if server in current.keys():
            update = current.copy()
            update.pop(server)
            self.write(update, current)
        else:
            self.server_not_found(server)

    def server_not_found(self, server):
        self.error(
            f"Service '{self.service}' contains no stored credentials for '{server}'"
        )

    def write(self, secrets, current):
        if current is None:
            current = self.read()

        for server in current.keys():
            if server not in secrets.keys():
                cmd = [
                    self.chamber,
                    "delete",
                    self.service,
                    encode_server(server),
                ]
                self.debug(f"{cmd}")
                check_call(cmd, env=self._env())
        for server, creds in secrets.items():
            cmd = [
                self.chamber,
                "write",
                self.service,
                encode_server(server),
                json.dumps(creds),
            ]
            self.debug(f"write: {cmd}")
            check_call(cmd, env=self._env())
        self.verify(secrets)

    def verify(self, secrets):
        self.debug(f"verify({secrets=})")
        timeout = time.time() + READBACK_TIMEOUT
        while time.time() < timeout:
            if self.read() == secrets:
                self.debug("verify() -> True")
                return True
            else:
                time.sleep(1)
        self.error(
            f"Readback failure writing credentials service '{self.service}'"
        )
        sys.exit(-1)

    def read(self):
        ret = {}
        services = check_output(
            [self.chamber, "list-services"], env=self._env()
        ).decode()
        services = services.split("\n")
        # self.debug(f"_read() {services=}")
        self.debug(
            f"_read() {self.service} in services: {self.service in services}"
        )
        if self.service in services:
            cmd = [self.chamber, "export", self.service]
            self.debug(f"{cmd}")
            data = check_output(cmd, env=self._env()).decode()
            self.debug(f"_read: {data=}")
            if len(data):
                for key, creds in json.loads(data).items():
                    if isinstance(creds, str):
                        creds = json.loads(creds)
                    ret[decode_key(key)] = creds
        self.debug(f"_read() -> {ret}")
        return ret


@click.group(name="docker-credential-chamber")
@click.version_option()
@click.option(
    "-s",
    "--service",
    type=str,
    show_envvar=True,
    envvar="DOCKER_CREDENTIALS_SERVICE",
    default="docker/credentials",
    help="chamber service name to use for credential store",
)
@click.option(
    "-t",
    "--token",
    type=str,
    show_envvar=True,
    envvar="DOCKER_CREDENTIALS_TOKEN",
    help="vault token to use with chamber command",
)
@click.option(
    "-d",
    "--debug",
    is_flag=True,
    envvar="DOCKER_CREDENTIALS_DEBUG",
    show_envvar=True,
    help="show full stack trace on exceptions",
)
@click.option(
    "-f",
    "--log-file",
    type=click.Path(dir_okay=False, writable=True),
    show_envvar=True,
    envvar="DOCKER_CREDENTIALS_LOGFILE",
    help="log to file",
)
@click.option(
    "-L",
    "--log-level",
    envvar="DOCKER_CREDENTIALS_LOGLEVEL",
    show_envvar=True,
    default="INFO",
)
@click.option(
    "-c", "--chamber", envvar="CHAMBER", show_envvar=True, default="chamber"
)
@click.pass_context
def cli(ctx, debug, service, token, chamber, log_file, log_level):
    """
    docker credential helper

    This program implements the credential helper protocol defined by docker
    for use by the 'docker login' command.  It uses 'chamber' to store the
    secrets so they are never written to ~/docker/config.json.
    (and preventing docker's warning)

    \b
    reference: https://docs.docker.com/engine/reference/commandline/login/#credential-helpers
    """

    # reference: https://docs.docker.com/engine/reference/commandline/login/#credential-helpers

    if debug:
        click.echo(f"{debug=}", err=True)
        click.echo(f"{service=}", err=True)
        click.echo(f"{token=}", err=True)
        click.echo(f"{chamber=}", err=True)
        click.echo(f"{log_file=}", err=True)
        click.echo(f"{log_level=}", err=True)

    if log_file:
        log_format = "%(levelname)s %(msg)s"
        if log_file == "stderr":
            logging.basicConfig(
                level=log_level, stream=sys.stderr, format=log_format
            )
        else:
            logging.basicConfig(
                level=log_level, filename=log_file, format=log_format
            )
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    handler = ExceptionHandler(debug, logger)  # noqa: F841
    ctx.obj = DCC(service, vault_token=token, chamber=chamber, logger=logger)
    ctx.obj.info("startup")


@cli.command()
@click.argument("input", type=click.File("r"), default="-")
@click.pass_context
def store(ctx, input):
    """protocol command"""
    ctx.obj.debug(f"store  {input=}")
    data = input.read()
    config = json.loads(data)
    ctx.obj.put(config["ServerURL"], config["Username"], config["Secret"])


@cli.command()
@click.argument("input", type=click.File("r"), default="-")
@click.argument("output", type=click.File("w"), default="-")
@click.pass_context
def get(ctx, input, output):
    """protocol command"""
    ctx.obj.debug(f"get {input=} {output=}")
    server_url = input.read().strip()
    json.dump(ctx.obj.get(server_url), output)


@cli.command()
@click.argument("input", type=click.File("r"), default="-")
@click.pass_context
def erase(ctx, input):
    """protocol command"""
    ctx.obj.debug(f"erase {input=}")
    server_url = input.read().strip()
    ctx.obj.delete(server_url)


@cli.command()
@click.argument("output", type=click.File("w"), default="-")
@click.pass_context
def list(ctx, output):
    """protocol command (undocumented)"""
    ctx.obj.debug(f"list {output=}")
    json.dump(ctx.obj.list(), output)


@cli.command()
@click.pass_context
def install(ctx):
    """configure this credental helper in ~/.docker/config.json"""
    ctx.obj.debug("install")
    ctx.obj.install()


if __name__ == "__main__":
    sys.exit(cli())
