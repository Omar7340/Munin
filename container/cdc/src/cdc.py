import paho.mqtt.client as mqtt
from datetime import datetime
import mysql.connector
import geopy.distance
import threading
import logging
import signal
import json
import time
import sys
import os


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


DATABASE_THREAD_1 = mysql.connector.connect(
    host=os.environ['MYSQL_HOST'],
    user=os.environ['MYSQL_USER'],
    password=os.environ['MYSQL_PASSWORD'],
    database=os.environ['MYSQL_DATABASE']
)


DATABASE_THREAD_2 = mysql.connector.connect(
    host=os.environ['MYSQL_HOST'],
    user=os.environ['MYSQL_USER'],
    password=os.environ['MYSQL_PASSWORD'],
    database=os.environ['MYSQL_DATABASE']
)


MOSQUITTO_SETTINGS = {
    "server": os.environ['MOSQUITTO_HOST'],
    "port": int(os.environ['MOSQUITTO_PORT']),
    "topics": [
        os.environ['MOSQUITTO_TOPIC_PERIODIQUE'],
        os.environ['MOSQUITTO_TOPIC_PONCTUELLE']
    ],
    "credentials": {
        "username": os.environ['MOSQUITTO_USER'],
        "password": os.environ['MOSQUITTO_PASSWORD'],
    }
}


#########################
### MOSQUITTO SETINGS ###
#########################


MOSQUITTO_CLIENT = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    """The callback for when the client receives a CONNACK response from the server.
    """
    logging.info(f"Attempt to connect to MQTT Broker...")
    if rc == 0:
        logging.info(f"Connected to MQTT Broker '{MOSQUITTO_SETTINGS['server']}:{MOSQUITTO_SETTINGS['port']}'")
        logging.info(f"Attempt to connect to topics...")
        for topic in MOSQUITTO_SETTINGS['topics']:
            client.subscribe(topic)
            logging.info(f"Client connected to topic '{topic}'")
    else:
        logging.error(f"Failed to MQTT Broker '{MOSQUITTO_SETTINGS['server']}:{MOSQUITTO_SETTINGS['port']}', return code {rc}\n")
        exit()


def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received from the server.
    """
    logging.info(f"New data arrived in the topic '{msg.topic}'")
    update_database(msg.topic, msg.payload)


def init_mosquitto():
    """Init the connection with mosquite server.
    """
    MOSQUITTO_CLIENT.username_pw_set(MOSQUITTO_SETTINGS['credentials']['username'], MOSQUITTO_SETTINGS['credentials']['password'])
    
    # set function callback
    MOSQUITTO_CLIENT.on_connect = on_connect
    MOSQUITTO_CLIENT.on_message = on_message

    # connect client to broker
    MOSQUITTO_CLIENT.connect(MOSQUITTO_SETTINGS['server'], MOSQUITTO_SETTINGS['port'])
    MOSQUITTO_CLIENT.loop_forever()


################
### DATABASE ###
################


def update_database(topic, data):
    """ Add data in database
    
    Parameters:
    ----------
        topic (str): name of the file broker
        data (str): data of the file broker (format in json)
        
    """
    data = json.loads(data)
    
    logging.info(f"Attempt to save data sent by car registered '{data['immatriculation']}' at '{datetime.fromtimestamp(int(data['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')}' to database...")
    if "periodique" in topic:
        logging.info(f"Data type is 'periodique'.")
        sql = "INSERT INTO CAR_EVENT (vitesse, geo_lat, geo_lon, timestamp_record, recorded_by) VALUES (%s, %s, %s, %s, %s)"
        val = (data['vitesse'], str(data['geo']['lat']), str(data['geo']['lon']), datetime.fromtimestamp(int(data['timestamp'])), data['immatriculation'])
        execute_request_sql(DATABASE_THREAD_1, sql, val)
    elif "ponctuelle" in topic:
        logging.info(f"Data type is 'ponctuelle'.")
        sql = "INSERT INTO TRAFFIC_EVENT (type, geo_lat, geo_lon, timestamp_occur, reported_by) VALUES (%s, %s, %s, %s, %s)"
        type_event = "accident" if data['accident'] else "accident"
        val = (type_event, str(data['geo']['lat']), str(data['geo']['lon']), datetime.fromtimestamp(int(data['timestamp'])), data['immatriculation'])
        execute_request_sql(DATABASE_THREAD_1, sql, val)
    else:
        sql = None
        val = None
    
    if sql and val: 
        logging.info(f"Data sent by car registered '{data['immatriculation']}' saved.")
    else:
        logging.warning(f"Data sent by car registered '{data['immatriculation']}' not saved.")


def execute_request_sql(connection, sql, val):
    """ Execute request SQL
    
    Parameters:
    ----------
        connection (MySQLConnection) : the connection MySQL
        sql (str): request to execute
        val (list): list of values to set in the request
        
    """
    # create cursor
    cursor = connection.cursor()
    # execute request sql
    cursor.execute(sql, val)
    # close cursor
    cursor.close()

    # commit in database
    connection.commit()
    

####################
### ANALYSE DATA ###
####################


def analyse_data():
    """ Analyse data to detected traffic event
    """
    while True:        
        logging.info(f"Attempt to retrieve car events to analyse from the database...")
        
        # create cursor
        cursor = DATABASE_THREAD_2.cursor()
        
        # execute request sql
        sql = """
            SELECT * FROM CAR_EVENT 
                WHERE 
                    vitesse < 90 AND 
                    analyzed = 0
                ORDER BY timestamp_record DESC
        """
        
        cursor.execute(sql)
        # get result request
        all_car_event = cursor.fetchall()
        
        if len(all_car_event) >= 2 : 
            logging.info(f"Data retrieve : {len(all_car_event)} car events.")
            
            logging.info(f"Analysing data to find traffic event to signale...")
            blacklist_id = []
            nb_traffic_event_find = 0
            for item in all_car_event:        
                # if car event is not yet blacklisted
                if item[0] not in blacklist_id:
                    car_event = [item]
                    
                    # blacklist temporary car event to avoid analyzing a second time
                    blacklist_id.append(item[0])
                    
                    # compare the car event with the others car events
                    for other in all_car_event:
                        if other[0] not in blacklist_id:
                            coords_item = (item[2], item[3])
                            coords_other = (other[2], other[3])
                            
                            # check the distance of the two cars events is lower than 500 meters
                            if geopy.distance.geodesic(coords_item, coords_other).m <= 500:
                                car_event.append(other)
                    
                    # check if there are at least 3 car events for create a traffic event (embouteillage)
                    if len(car_event) >= 3:
                        # create a traffic event (embouteillage)
                        create_traffic_event("embouteillage", car_event[0][2], car_event[0][3], car_event[0][4], "cdc")
                        # update counter of traffic event created
                        nb_traffic_event_find += 1
                        # disable car events to avoid analyzing them a second time
                        for event in car_event:
                            set_car_event_analyzed(event[0])            
            
            logging.info(f"Data analysis completed.")
            logging.info(f"Number of traffic events created : {nb_traffic_event_find}")
        else:
            logging.info(f"No car events to analyse.")
        
        # close cursor
        cursor.close()
        
        # sleep the processus
        time.sleep(10)
    

def create_traffic_event(type_event, lat, lon, timestamp, reported_by):
    """Create a traffic event 
    
    Parameters:
    ----------
        type_event (str): type of the traffic event 
        lat (str): latitude of the traffic event 
        lon (str): longitude of the traffic event
        timestamp (str): timestamp of the traffic event 
        reported_by (str): person who report the traffic event 
        
    """
    sql = "INSERT INTO TRAFFIC_EVENT (type, geo_lat, geo_lon, timestamp_occur, reported_by) VALUES (%s, %s, %s, %s, %s)"
    val = (type_event, lat, lon, timestamp, reported_by)

    execute_request_sql(DATABASE_THREAD_2, sql, val)


def set_car_event_analyzed(id):
    """Update car event to analyzed
    
    Parameter:
    ----------
        id (int): identifier of the car event 
        
    """
    sql = """
        UPDATE CAR_EVENT 
            SET analyzed = 1 
                WHERE id = %s
    """
    val = (id,)

    execute_request_sql(DATABASE_THREAD_2, sql, val)
        
        
############
### MAIN ###
############


def signal_handler(sig, frame):
    MOSQUITTO_CLIENT.disconnect()
    DATABASE_THREAD_1.close()
    DATABASE_THREAD_2.close()
    sys.exit()


signal.signal(signal.SIGINT, signal_handler)


def run():
    """ Execute program cdc
    """
    threads = []
    
    # Thread for get data on MQTT Broker
    threads.append(threading.Thread(target=init_mosquitto))
    
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
    
