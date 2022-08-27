# docker-credential-chamber

An implementation of a credential helper for 'docker login' using `chamber` for the backend storage

reference: https://docs.docker.com/engine/reference/commandline/login/#credential-helpers


## CLI

```
Usage: docker-credential-chamber [OPTIONS] COMMAND [ARGS]...

  docker credential helper

  This program implements the credential helper protocol defined by docker for
  use by the 'docker login' command.  It uses 'chamber' to store the secrets
  so they are never written to ~/docker/config.json. (and preventing docker's
  warning)

  reference: https://docs.docker.com/engine/reference/commandline/login/#credential-helpers

Options:
  -s, --service TEXT    chamber service name to use for credential store  [env
                        var: DOCKER_CREDENTIALS_SERVICE]
  -t, --token TEXT      vault token to use with chamber command  [env var:
                        DOCKER_CREDENTIALS_TOKEN]
  -d, --debug           show full stack trace on exceptions
  -f, --log-file FILE   log to file  [env var: DOCKER_CREDENTIALS_LOGFILE]
  -e, --log-stderr      log to stderr
  -L, --log-level TEXT  [env var: DOCKER_CREDENTIALS_LOGLEVEL]
  --help                Show this message and exit.

Commands:
  erase    protocol command
  get      protocol command
  install  configure this credental helper in ~/.docker/config.json
  list     protocol command (undocumented)
  store    protocol command
```
