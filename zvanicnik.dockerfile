FROM python:3

RUN mkdir -p /opt/src/zvanicnik
WORKDIR opt/src/zvanicnik

COPY zvanicnik/requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY zvanicnik/application.py ./application.py
COPY zvanicnik/configuration.py ./configuration.py
COPY zvanicnik/models.py ./models.py

ENTRYPOINT ["python", "./application.py"]