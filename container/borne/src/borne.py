import sys
import os
import logging
import json
import paho.mqtt.client as mqtt
import random
import time


#########################
### LOG CONFIGURATION ###
#########################

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s : %(message)s',
    handlers=[
        logging.FileHandler("borne.log"),
        logging.StreamHandler()
    ]
)

##############################
### ENVIRONNEMENT SETTINGS ###
##############################

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

def on_connect(client, userdata, flags, rc):
    """The callback for when the client receives a CONNACK response from the server.
    """
    
    logging.info(f"Attempt to connect to MQTT Broker...")
    if rc == 0:
        logging.info(f"Connected to MQTT Broker '{MOSQUITTO_SETTINGS['server']}:{MOSQUITTO_SETTINGS['port']}'")
    else:
        logging.error(f"Failed to MQTT Broker '{MOSQUITTO_SETTINGS['server']}:{MOSQUITTO_SETTINGS['port']}', return code {rc}\n")
        exit()

def connect_broker():
    client = mqtt.Client()
    client.username_pw_set(MOSQUITTO_SETTINGS['credentials']['username'], MOSQUITTO_SETTINGS['credentials']['password'])
    
    # set function callback
    client.on_connect = on_connect

    # connect client to broker
    client.connect(MOSQUITTO_SETTINGS['server'], MOSQUITTO_SETTINGS['port'])

    return client

######################
### PLAY SCENARIOS ###
######################

def play_data(file):
    logging.info(f"Opening file '{file}' ...")
    try:
        f = open(file)
        logging.info(f"File opened: '{file}'")
        logging.info(f"Load JSON data from file: '{file}'")
        data = json.load(f)
        send_data(data)

        logging.info(f"Closing file: '{file}'")
        f.close()

    except IOError:
        logging.error(f"Failed to find or read: '{file}'")

def send_data(json_data):
    client = connect_broker()

    msg_count = 0
    msg_error = 0

    count_until_pause = 200
    count_temp = 0

    for data in json_data['packets']:
        if data['type'] == "periodique":
            topic = MOSQUITTO_SETTINGS['topics'][0]
        elif data['type'] == "ponctuelle":
            topic = MOSQUITTO_SETTINGS['topics'][1]
        else:
            logging.error(f"JSON Data bad construction => file: '{file}'")
            msg_error += 1
        
        data = json.dumps(data, indent=4)

        logging.info(f"Sending data to topic '{topic}'")
        result = client.publish(topic, data)
    
        status = result[0]
        if status == 0:
            print(f"Message `{msg_count+1}` has been sent to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
    
        if count_temp == count_until_pause:
            count_temp = 0
            time.sleep(3)

        msg_count += 1
        count_temp +=1

    logging.info(f"'{msg_count}' messages published with '{msg_error}' errors")


############
### MAIN ###
############


def run():
    """ Execute program borne
    """
    data_file = sys.argv[1]

    if os.path.isfile(data_file):
        play_data(data_file)
    else:
        for filename in os.listdir(data_file):
            play_data(data_file + "/" +filename)


if __name__ == '__main__':
    run()