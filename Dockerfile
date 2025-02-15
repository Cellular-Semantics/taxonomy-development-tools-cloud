FROM ubuntu:22.04

ENV WORKSPACE=/code
ENV HTTPS=False
ENV TAXONOMIES_VOLUME=$WORKSPACE/taxonomies

ENV GITHUB_TOKEN=provide_token
ENV TDT_URL_PREFIX=""

RUN apt-get update
RUN apt-get install -y curl unzip
RUN apt-get install -y git
RUN apt-get install -y sqlite3 libsqlite3-dev
RUN apt-get install -y mariadb-client
RUN apt-get install -y python3-pip
RUN apt-get install -y openjdk-11-jre-headless
RUN apt-get install -y make

RUN mkdir -p $WORKSPACE $WORKSPACE/tdt_api $TAXONOMIES_VOLUME
ADD requirements.txt setup.py logging.conf $WORKSPACE/

RUN pip install -r /code/requirements.txt
# copy except __init__.py file and test folder
ADD src/tdt_api/endpoints $WORKSPACE/tdt_api/endpoints
ADD src/tdt_api/exception $WORKSPACE/tdt_api/exception
ADD src/tdt_api/utils $WORKSPACE/tdt_api/utils
ADD src/tdt_api/app.py src/tdt_api/restx.py $WORKSPACE/tdt_api/

RUN apt-get update &&  \
    apt-get install -y aha \
    sqlite3 \
    python3-psycopg2

WORKDIR $WORKSPACE

RUN cd $WORKSPACE && python3 setup.py develop
RUN ls -l /code && ls -l $WORKSPACE/tdt_api

VOLUME $WORKSPACE/taxonomies

ENTRYPOINT bash -c "cd /code; python3 tdt_api/app.py"