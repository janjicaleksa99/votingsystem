FROM python:3

RUN mkdir -p /opt/src/admin
WORKDIR opt/src/admin

COPY admin/requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY admin/migrate.py ./migrate.py
COPY admin/configuration.py ./configuration.py
COPY admin/models.py ./models.py

ENTRYPOINT ["sleep", "36"]
ENTRYPOINT ["python", "./migrate.py"]