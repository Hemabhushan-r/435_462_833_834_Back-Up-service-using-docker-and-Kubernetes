FROM python:3

WORKDIR /app


COPY ./backup.py /app/backup.py

COPY ./requirements.txt /app/requirements.txt


RUN pip install --no-cache-dir -r requirements.txt



CMD [ "python3","backup.py" ] 


