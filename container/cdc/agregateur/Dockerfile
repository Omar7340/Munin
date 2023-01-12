FROM python:3.9-alpine

WORKDIR /usr/src/app

COPY ./src/ .

RUN pip install -Ur requirements.txt

ENTRYPOINT [ "python", "agregateur.py" ]