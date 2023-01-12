FROM python:3.9-alpine

WORKDIR /usr/src/app

COPY ./src/ .

RUN pip install -Ur requirements.txt

ENTRYPOINT [ "python", "borne.py", "scenarios/aleatoires/DATAS_ALEA_MIX_LOURD.json" ]