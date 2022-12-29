#!/usr/bin/env python3

import json
import logging
import os
import sys
from base64 import b64decode, b64encode
from pathlib import Path
from subprocess import check_call, check_output
from tempfile import SpooledTemporaryFile

import click

from .exception_handler import ExceptionHandler

DISABLE_LOGGING = True


def encode_server(server):
    return b64encode(server.encode()).decode()


def decode_key(key):
    return b64decode(key.encode()).decode()


class Secrets:
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
        self.secrets = None
        self.logger = logger

    def info(self, *args, **kwargs):
        if self.logger:
            self.logger.info(*args, **kwargs)

    def debug(self, *args, **kwargs):
        if self.logger:
            self.logger.debug(*args, **kwargs)

    def _env(self):
        ret = os.environ.copy()
        if self.vault_token:
            ret["VAULT_TOKEN"] = self.vault_token
        if self.vault_addr:
            ret["VAULT_ADDR"] = self.vault_addr
        return ret

    def get(self, server):
        if self.secrets is None:
            self.read()
        return self.secrets.get(encode_server(server), None)

    def put(self, server, username, secret):
        if self.secrets is None:
            self.read()
        server = encode_server(server)
        self.secrets[server] = {"Username": username, "Secret": secret}
        self.write()

    def list(self):
        if self.secrets is None:
            self.read()
        return {decode_key(k): v["Username"] for k, v in self.secrets.items()}

    def delete(self, server):
        if self.secrets is None:
            self.read()
        server = encode_server(server)
        if server in self.secrets:
            del self.secrets[server]
        self.write()

    def write(self, fp=None):
        if self.secrets is None:
            self.read()
        if fp:
            write_data = json.dumps(self.secrets, indent=2)
            self.debug(f"write: {write_data}")
            write_data = write_data + "\n"
            fp.write(write_data.encode())
        else:
            for key in self._read().keys():
                cmd = [self.chamber, "delete", self.service, key]
                self.debug(f"{cmd}")
                check_call(cmd, env=self._env())
            with SpooledTemporaryFile() as fp:
                fp.write(json.dumps(self.secrets).encode())
                fp.seek(0)
                docker_data = fp.read()
                self.debug(f"write: {docker_data.decode()}")

                creds = json.loads(docker_data)
                for k, v in creds.items():
                    cmd = [
                        self.chamber,
                        "write",
                        self.service,
                        k,
                        json.dumps(v),
                    ]
                    self.debug(f"{cmd}")
                    check_call(cmd, env=self._env())

    def read(self, fp=None):
        self.secrets = {}
        if fp:
            local_data = fp.read()
            self.debug(f"read: {local_data}")
            self.secrets = json.loads(local_data)
        else:
            self.secrets = self._read()

    def _read(self):
        ret = {}
        services = check_output(
            [self.chamber, "list-services"], env=self._env()
        ).decode()
        services = services.split("\n")
        if self.service in services:
            cmd = [self.chamber, "export", self.service]
            self.debug(f"{cmd}")
            data = check_output(cmd, env=self._env()).decode()
            self.debug(f"_read: {data}")
            if len(data):
                creds = json.loads(data)
                ret = {}
                for k, v in creds.items():
                    if isinstance(v, str):
                        v = json.loads(v)
                    ret[k] = v
        self.debug(f"_read()-> {ret}")
        return ret


@click.group(name="docker-credential-chamber")
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
def cli(ctx, service, token, debug, log_file, log_level, chamber):
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

    if DISABLE_LOGGING:
        logger = None
    elif log_file:
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
    else:
        logger = None

    handler = ExceptionHandler(debug, logger)  # noqa: F841

    ctx.obj = Secrets(
        service, vault_token=token, chamber=chamber, logger=logger
    )

    ctx.obj.info("startup")


# @cli.command()
# @click.argument("output", type=click.File("w"), default="-")
# @click.pass_context
# def dump(ctx, output):
#    logging.debug(f"dump {output=}")
#    ctx.obj.write(output)


# @cli.command()
# @click.argument("input", type=click.File("r"), default="-")
# @click.pass_context
# def load(ctx, input):
#    logging.debug(f"load {input=}")
#    ctx.obj.read(input)
#    ctx.obj.write()


# @cli.command()
# @click.argument("server-url")
# @click.argument("username")
# @click.argument("secret")
# @click.pass_context
# def init(ctx, server_url, username, secret):
#    logging.debug(f"init {server_url=} {username=} {secret=}")
#    ctx.obj.put(server_url, username, secret)


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
    config_dir = Path.home() / ".docker"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    if config_file.is_file():
        config = json.loads(config_file.read_text())
    else:
        config = {}
    config["credsStore"] = "chamber"
    config_file.write_text(json.dumps(config))


if __name__ == "__main__":
    sys.exit(cli())
