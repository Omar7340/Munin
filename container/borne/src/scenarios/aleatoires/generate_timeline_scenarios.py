import generate_scenarios_coherent
from datetime import datetime
from datetime import timedelta
import random
import json

def run():
    # Creer une timeline de timestamp
    # sur 14 semaines de datas
    # 24 scenarios aleatoires par jour
    # 300 lignes par scenarios
    # Total de 300*24*7*14: 617400 paquets 

    # debut le 01/09/2022 a 8h30
    # start_datetime = datetime(2022,9,1,8,30)
    # end_datetime = datetime(2022,9,30,20,30)

    # start_datetime = datetime(2022,10,1,8,30)
    # end_datetime = datetime(2022,10,31,20,30)
    
    start_datetime = datetime(2022,11,1,8,30)
    end_datetime = datetime(2022,11,30,20,30)

    date = start_datetime

    packets = []

    while date < end_datetime: 

        date_timestamp = str(round(datetime.timestamp(date)))

        n_perio= random.randint(0,50)
        n_ponct= random.randint(0,10)
        n_pont_close= random.randint(0,5)
        n_embouteillage= random.randint(0,25)


        for i in range(n_perio-n_embouteillage):
            packets = packets + generate_scenarios_coherent.generate_packet_perio(isembouteillage=False, timestamp=date_timestamp)

        for i in range(n_ponct-(n_pont_close*2)):
            packets = packets + generate_scenarios_coherent.generate_packet_ponct(close=False, timestamp=date_timestamp)
        
        for i in range(n_pont_close):
            packets = packets + generate_scenarios_coherent.generate_packet_ponct(close=True, timestamp=date_timestamp)
        
        for i in range(n_embouteillage):
            packets = packets + generate_scenarios_coherent.generate_packet_perio(isembouteillage=True, timestamp=date_timestamp)
        
        date = date + timedelta(hours=1)
    
    res = { 'packets': packets }

    # json to file
    json_object = json.dumps(res, separators=(',', ':'))

    date = date.strftime("%Y%m")

    filename = f"timeline/DATAS_ALEA_MIX_{date}.json"
    
    with open(filename, "w") as outfile:
        outfile.write(json_object)

if __name__ == '__main__':
    run()