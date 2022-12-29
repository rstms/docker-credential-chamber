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


def encode_server(server):
    return b64encode(server.encode()).decode()


def decode_key(key):
    return b64decode(key.encode()).decode()


class Secrets:
    def __init__(self, service, vault_token=None, vault_addr=None, chamber=None):
        self.service = service
        self.vault_token = vault_token
        self.vault_addr = vault_addr
        self.chamber = chamber or 'chamber'
        self.secrets = None

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
        s = self.secrets.setdefault(server, {})
        s["Username"] = username
        s["Secret"] = secret
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
            json.dump(self.secrets, fp, indent=2)
            fp.write("\n")
        else:
            for key in self._read().keys():
                check_call(
                    [self.chamber, "delete", self.service, key], env=self._env()
                )
            with SpooledTemporaryFile() as fp:
                fp.write(json.dumps(self.secrets).encode())
                fp.seek(0)
                check_call(
                    [self.chamber, "import", self.service, "-"],
                    stdin=fp,
                    env=self._env(),
                )

    def read(self, fp=None):
        self.secrets = {}
        if fp:
            self.secrets = json.load(fp)
        else:
            self.secrets = self._read()

    def _read(self):
        data = check_output(
            [self.chamber, "--if-exists", "export", self.service], env=self._env()
        ).decode()
        if len(data):
            ret = json.loads(data)
        else:
            ret = {}
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
    "-d", "--debug", is_flag=True, help="show full stack trace on exceptions"
)
@click.option(
    "-f",
    "--log-file",
    type=click.Path(dir_okay=False, writable=True),
    show_envvar=True,
    envvar="DOCKER_CREDENTIALS_LOGFILE",
    help="log to file",
)
@click.option("-e", "--log-stderr", is_flag=True, help="log to stderr")
@click.option(
    "-L",
    "--log-level",
    envvar="DOCKER_CREDENTIALS_LOGLEVEL",
    show_envvar=True,
    default="INFO",
)
@click.option('-c', '--chamber', envvar='CHAMBER', show_envvar=True, default='chamber')
@click.pass_context
def cli(ctx, service, token, debug, log_file, log_stderr, log_level, chamber):
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

    log_format = "%(levelname)s %(msg)s"
    if log_file:
        logging.basicConfig(
            level=log_level, filename=log_file, format=log_format
        )
        logger = logging.getLogger()
    elif log_stderr:
        logging.basicConfig(
            level=log_level, stream=sys.stderr, format=log_format
        )
        logger = logging.getLogger()
    else:
        logger = None

    handler = ExceptionHandler(debug, logger)  # noqa: F841

    logging.info("startup")
    ctx.obj = Secrets(service, vault_token=token, chamber=chamber)


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
    logging.debug(f"store  {input=}")
    data = input.read()
    config = json.loads(data)
    ctx.obj.put(config["ServerURL"], config["Username"], config["Secret"])


@cli.command()
@click.argument("input", type=click.File("r"), default="-")
@click.argument("output", type=click.File("w"), default="-")
@click.pass_context
def get(ctx, input, output):
    """protocol command"""
    logging.debug(f"get {input=} {output=}")
    server_url = input.read().strip()
    json.dump(ctx.obj.get(server_url), output)


@cli.command()
@click.argument("input", type=click.File("r"), default="-")
@click.pass_context
def erase(ctx, input):
    """protocol command"""
    logging.debug(f"erase {input=}")
    server_url = input.read().strip()
    ctx.obj.delete(server_url)


@cli.command()
@click.argument("output", type=click.File("w"), default="-")
@click.pass_context
def list(ctx, output):
    """protocol command (undocumented)"""
    logging.debug(f"list {output=}")
    json.dump(ctx.obj.list(), output)


@cli.command()
@click.pass_context
def install(ctx):
    """configure this credental helper in ~/.docker/config.json"""
    logging.debug("install")
    config_file = Path.home() / ".docker" / "config.json"
    if config_file.is_file():
        config = json.loads(config_file.read_text())
    else:
        config = {}
    config["credsStore"] = "chamber"
    config_file.write_text(json.dumps(config))


if __name__ == "__main__":
    sys.exit(cli())
