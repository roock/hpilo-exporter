FROM python:3.10.1-alpine3.15
ADD . /usr/src/hpilo_exporter
RUN pip install -e /usr/src/hpilo_exporter
ENTRYPOINT ["hpilo-exporter"]
EXPOSE 9416
