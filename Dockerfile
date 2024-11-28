FROM ubuntu:22.04

ENV WORKSPACE=/code
ENV HTTPS=False

RUN apt-get update
RUN apt-get install -y curl unzip
RUN apt-get install -y sqlite3 libsqlite3-dev
RUN apt-get install -y mariadb-client
RUN apt-get install -y python3-pip
RUN apt-get install -y openjdk-11-jre-headless
RUN apt-get install -y make

RUN mkdir $WORKSPACE $WORKSPACE/tdt_api
ADD requirements.txt setup.py logging.conf $WORKSPACE/

RUN pip install -r /code/requirements.txt
# copy except __init__.py file and test folder
ADD src/tdt_api/endpoints $WORKSPACE/tdt_api/endpoints
ADD src/tdt_api/exception $WORKSPACE/tdt_api/exception
ADD src/tdt_api/app.py src/tdt_api/restx.py $WORKSPACE/tdt_api/

RUN apt-get update &&  \
    apt-get install -y aha \
    sqlite3 \
    python3-psycopg2

# install nanobot
RUN curl -L -k -o /bin/nanobot 'https://github.com/ontodev/nanobot.rs/releases/download/v2023-10-26/nanobot-x86_64-unknown-linux-musl'
RUN chmod +x /bin/nanobot

WORKDIR $WORKSPACE

RUN cd $WORKSPACE && python3 setup.py develop
RUN ls -l /code && ls -l $WORKSPACE/tdt_api

VOLUME $WORKSPACE/taxonomies

ENTRYPOINT bash -c "cd /code; python3 tdt_api/app.py"