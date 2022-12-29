FROM python:3.10.4-slim-buster
RUN pip install pipx
RUN pipx ensurepath
RUN pipx install docker-credential-chamber
CMD [ "/bin/bash", "-l", "-c", "docker-credential-chamber" ]
