FROM python:3

RUN mkdir -p /opt/src/authentication
WORKDIR opt/src/authentication

COPY authentication/requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY authentication/migrate.py ./migrate.py
COPY authentication/configuration.py ./configuration.py
COPY authentication/models.py ./models.py

ENTRYPOINT ["sleep", "36"]
ENTRYPOINT ["python", "./migrate.py"]