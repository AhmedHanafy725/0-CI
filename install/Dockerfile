From ubuntu:18.04
RUN apt-get update && apt-get install -y wget git python3-pip python3-venv redis-server tmux nginx cron nodejs npm
RUN pip3 install poetry
RUN mkdir -p /sandbox/code/github/threefoldtech
RUN git clone https://github.com/threefoldtech/js-ng.git /sandbox/code/github/threefoldtech/js-ng 
RUN git clone https://github.com/threefoldtech/zeroCI.git /sandbox/code/github/threefoldtech/zeroCI
WORKDIR /sandbox/code/github/threefoldtech/js-ng
RUN poetry config virtualenvs.create false && poetry install
RUN poetry shell
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
WORKDIR /sandbox/code/github/threefoldtech/zeroCI
RUN pip3 install -r install/requirement.txt
RUN cd frontend && npm install
RUN cd frontend && npm run build
CMD /bin/bash install/startup.sh
