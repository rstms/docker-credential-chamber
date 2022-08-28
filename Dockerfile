FROM python:3.10.4-slim-buster
RUN pipx install docker-credentaial-helper
CMD docker-credential-helper
