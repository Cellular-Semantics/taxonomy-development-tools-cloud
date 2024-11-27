FROM python:3.9.10-slim

ENV HTTPS=False

RUN mkdir /code /code/src /code/tdt_api
ADD requirements.txt run.sh setup.py logging.conf /code/

RUN chmod 777 /code/run.sh
RUN pip install -r /code/requirements.txt
# copy except __init__.py file and test folder
ADD src/tdt_api/endpoints /code/tdt_api/endpoints
ADD src/tdt_api/exception /code/tdt_api/exception
ADD src/tdt_api/app.py src/tdt_api/restplus.py /code/tdt_api/

WORKDIR /code

RUN cd /code && python3 setup.py develop
RUN ls -l /code && ls -l /code/tdt_api

ENTRYPOINT bash -c "cd /code; python3 tdt_api/app.py"