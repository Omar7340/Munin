FROM python:3.9-alpine

WORKDIR /usr/src/app

COPY ./src/ .

RUN pip install -Ur requirements.txt
# RUN python scenarios/aleatoires/generate_scenarios_coherent.py 200 10 5 9 datas.json
# RUN python scenarios/aleatoires/generate_scenarios_coherent.py

# ENTRYPOINT [ "python", "borne.py", "DATAS_ALEA_MIX_30_9_3_5.json" ]

ENTRYPOINT [ "python", "borne.py", "scenarios/aleatoires/timeline/" ]