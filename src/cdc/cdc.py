# Deux grandes tâches qui s'executent en parellèle (Thread)
#  - Connexion au fil mosquito et récupération des données puis stockage dans la bdd
#  - Ecoute sur la bdd et dès qu'il y a un ajout dans la bdd executer les analyse
from signal import signal, SIGINT
from sys import exit
import paho.mqtt.client as mqtt
import mysql.connector
import threading
import logging
from datetime import datetime
import json
import geopy.distance


#########################
### LOG CONFIGURATION ###
#########################

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s : %(message)s',
    handlers=[
        logging.FileHandler("cdc.log"),
        logging.StreamHandler()
    ]
)

##############################
### ENVIRONNEMENT SETTINGS ###
##############################

DATABASE = mysql.connector.connect(
    host="grafana_db",
    user="dev",
    password="dev",
    database="CONTROLE_TRAFFIC"
)

MOSQUITTO_SETTINGS = {
    "server": "test.mosquitto.org",
    "port": 1883,
    "topics": [
        "/data/periodique",
        "/data/ponctuelle",
    ],
    "client_id": "cdc",
    "credentials": {
        "username": "admin",
        "password": "admin",
    }
}

#########################
### MOSQUITTO SETINGS ###
#########################


def on_connect(client, userdata, flags, rc):
    """The callback for when the client receives a CONNACK response from the server.
    """
    
    logging.info(f"Attempt to connect to MQTT Broker...")
    if rc == 0:
        logging.info(f"Connected to MQTT Broker '{MOSQUITTO_SETTINGS['server']}:{MOSQUITTO_SETTINGS['port']}'")
        logging.info(f"Attempt to connect to topics...")
        for topic in MOSQUITTO_SETTINGS['topics']:
            client.subscribe(topic)
            logging.info(f"Client '{MOSQUITTO_SETTINGS['client_id']}' connected to topic '{topic}'")
    else:
        logging.error(f"Failed to MQTT Broker '{MOSQUITTO_SETTINGS['server']}:{MOSQUITTO_SETTINGS['port']}', return code {rc}\n")
        exit()


def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received from the server.
    """
    
    logging.info(f"New data arrived in the topic '{msg.topic}'")
    update_database(msg.topic, msg.payload)


def connect_broker():
    client = mqtt.Client()
    client.username_pw_set(MOSQUITTO_SETTINGS['credentials']['username'], MOSQUITTO_SETTINGS['credentials']['password'])
    
    # set function callback
    client.on_connect = on_connect
    client.on_message = on_message

    # connect client to broker
    client.connect(MOSQUITTO_SETTINGS['server'], MOSQUITTO_SETTINGS['port'])
    client.loop_forever()


################
### DATABASE ###
################


def update_database(topic, data):
    """ Add data in database
    
    Parameter:
    ----------
        topic (str): name of the file broker
        data (str): data of the file broker (format in json)
        
    """
    
    data = json.loads(data)
    mycursor = DATABASE.cursor()
    
    logging.info(f"Attempt to save data sent by car registered '{data['immatriculation']}' at '{datetime.fromtimestamp(int(data['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')}' to database...")
    if "periodique" in topic:
        logging.info(f"Data type is 'periodique'.")
        sql = "INSERT INTO CAR_EVENT (vitesse, geo_lat, geo_lon, timestamp_record, recorded_by) VALUES (%s, %s, %s, %s, %s)"
        val = (data['vitesse'], data['geo']['lat'], data['geo']['lon'], data['timestamp'], data['immatriculation'])
    elif "ponctuelle" in topic:
        logging.info(f"Data type is 'ponctuelle'.")
        sql = "INSERT INTO TRAFFIC_EVENT (type, geo_lat, geo_lon, timestamp_occur, recorded_by) VALUES (%s, %s, %s, %s, %s)"
        type_event = "accident" if data['accident'] else "accident"
        val = (type_event, data['geo']['lat'], data['geo']['lon'], data['timestamp'], data['immatriculation'])
        
    mycursor.execute(sql, val)
    DATABASE.commit()
    
    logging.info(f"Data sent by car registered '{data['immatriculation']}' saved.")
    

####################
### ANALYSE DATA ###
####################


def analyse_data():
    """ Analyse data to detected traffic event
    """
        
    mycursor = DATABASE.cursor()
    
    logging.info(f"Attempt to retrieve the last 100 car events with conditions from the database...")
    sql = """
        SELECT * FROM CAR_EVENT 
            WHERE 
                vitesse < 90 AND 
                analysed = 0 AND
                timestamp_record >= NOW() - INTERVAL 10 MINUTE
            ORDER BY timestamp_record DESC 
            LIMIT 100 
            GROUP BY(recorded_by)
    """
    mycursor.execute(sql)
    all_car_event = mycursor.fetchall()
    logging.info(f"Data retrieve : {len(all_car_event)} car events.")
    
    logging.info(f"Analysing data to find traffic event to signale...")
    blacklist_tmp = []
    nb_traffic_event_find = 0
    for item in all_car_event:
        # if car event is not yet blacklisted
        if item['id'] not in blacklist_tmp:
            car_event = [item]
            
            # compare the car event with the others car events
            for other in all_car_event:
                coords_item = (item['geo_lat'], item['geo_lon'])
                coords_other = (other['geo_lat'], other['geo_lon'])
                
                # check the distance of the two cars events is lower than 500 meters
                if geopy.distance.geodesic(coords_item, coords_other).m <= 500:
                    car_event.append(other)
            
            # check if there are at least 3 car events for create a traffic event (embouteillage)
            if len(car_event) >= 3:
                # create a traffic event (embouteillage)
                create_traffic_event("embouteillage", car_event[0]['geo_lat'], car_event[0]['geo_lon'], car_event[0]['timestamp_record'], "cdc")
                # update counter of traffic event created
                nb_traffic_event_find += 1
                # disable car events to avoid analyzing them a second time
                for event in car_event:
                    set_car_event_analysed(event['id'])
                
            
            # blacklist temporary car event to avoid analyzing a second time
            blacklist_tmp.append(item['id'])
    
    logging.info(f"Data analysis completed.")
    logging.info(f"Number of traffic events created : {nb_traffic_event_find}")
        

def create_traffic_event(type_event, lat, lon, timestamp, reported_by):
    """Create a traffic event 
    
    Parameter:
    ----------
        type_event (str): type of the traffic event 
        lat (str): latitude of the traffic event 
        lon (str): longitude of the traffic event
        timestamp (str): timestamp of the traffic event 
        reported_by (str): person who report the traffic event 
        
    """
    mycursor = DATABASE.cursor()
    
    sql = "INSERT INTO TRAFFIC_EVENT (type, geo_lat, geo_lon, timestamp_occur, recorded_by) VALUES (%s, %s, %s, %s, %s)"
    val = (type_event, lat, lon, timestamp, reported_by)

    mycursor.execute(sql, val)
    DATABASE.commit()


def set_car_event_analysed(id):
    """Udpate car event to analysed
    
    Parameter:
    ----------
        id (str): identifier of the car event 
        
    """
    
    mycursor = DATABASE.cursor()
    
    sql = """
        UPDATE CAR_EVENT 
            SET analysed = 1 
                WHERE id = %s
    """
    val = (id)

    mycursor.execute(sql, val)
    DATABASE.commit()


############
### MAIN ###
############


def run():
    """ Execute program cdc
    """
    threads = []
    
    # Thread for get data on MQTT Broker
    threads.append(threading.Thread(target=connect_broker))
    
    # Thread for analasy data
    threads.append(threading.Thread(target=analyse_data))
    
    # start all threads
    for x in threads:
        x.start()

    # wait end of all threads
    for x in threads:
        x.join()


if __name__ == '__main__':
    run()