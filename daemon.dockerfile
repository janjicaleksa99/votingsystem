FROM python:3

RUN mkdir -p /opt/src/daemon
WORKDIR opt/src/daemon

COPY daemon/requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY daemon/application.py ./application.py
COPY daemon/configuration.py ./configuration.py
COPY daemon/models.py ./models.py

ENTRYPOINT ["python", "./application.py"]