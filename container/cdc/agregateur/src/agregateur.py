import paho.mqtt.client as mqtt
from datetime import datetime
import mysql.connector
import logging
import signal
import json
import sys
import os


#########################
### LOG CONFIGURATION ###
#########################


logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s : %(message)s',
    handlers=[
        logging.FileHandler("cdc-agregateur.log"),
        logging.StreamHandler()
    ]
)


##############################
### ENVIRONNEMENT SETTINGS ###
##############################


DATABASE = mysql.connector.connect(
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
        execute_request_sql(sql, val)
    elif "ponctuelle" in topic:
        logging.info(f"Data type is 'ponctuelle'.")
        sql = "INSERT INTO TRAFFIC_EVENT (type, geo_lat, geo_lon, timestamp_occur, reported_by) VALUES (%s, %s, %s, %s, %s)"
        type_event = "accident" if data['accident'] else "accident"
        val = (type_event, str(data['geo']['lat']), str(data['geo']['lon']), datetime.fromtimestamp(int(data['timestamp'])), data['immatriculation'])
        execute_request_sql(sql, val)
    else:
        sql = None
        val = None
    
    if sql and val: 
        logging.info(f"Data sent by car registered '{data['immatriculation']}' saved.")
    else:
        logging.warning(f"Data sent by car registered '{data['immatriculation']}' not saved.")


def execute_request_sql(sql, val):
    """ Execute request SQL
    
    Parameters:
    ----------
        connection (MySQLConnection) : the connection MySQL
        sql (str): request to execute
        val (list): list of values to set in the request
        
    """
    # create cursor
    cursor = DATABASE.cursor()
    # execute request sql
    cursor.execute(sql, val)
    # close cursor
    cursor.close()

    # commit in database
    DATABASE.commit()
        
        
############
### MAIN ###
############


def signal_handler(sig, frame):
    MOSQUITTO_CLIENT.disconnect()
    DATABASE.close()
    sys.exit()


signal.signal(signal.SIGINT, signal_handler)


if __name__ == '__main__':
    init_mosquitto()
    
