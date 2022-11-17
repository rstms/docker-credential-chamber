FROM python:3.10.4-slim-buster
RUN pipx install docker-credential-helper
CMD docker-credential-helper
