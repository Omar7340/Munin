import mysql.connector
import geopy.distance
import logging
import time
import os


#########################
### LOG CONFIGURATION ###
#########################


logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s : %(message)s',
    handlers=[
        logging.FileHandler("cdc-analyseur.log"),
        logging.StreamHandler()
    ]
)


################
### DATABASE ###
################


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
    

def create_traffic_event(connection, type_event, lat, lon, timestamp, reported_by):
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

    execute_request_sql(connection, sql, val)


def set_car_event_analyzed(connection, id):
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

    execute_request_sql(connection, sql, val)
        

############
### MAIN ###
############


def analyse_data():
    """ Analyse data to detected traffic event
    """
    while True:        
        logging.info(f"Attempt to retrieve car events to analyse from the database...")
        
        # create database connection
        database = mysql.connector.connect(
            host=os.environ['MYSQL_HOST'],
            user=os.environ['MYSQL_USER'],
            password=os.environ['MYSQL_PASSWORD'],
            database=os.environ['MYSQL_DATABASE'],
        )
        
        # create cursor
        cursor = database.cursor()
        
        sql = """
            SELECT * FROM CAR_EVENT 
                WHERE 
                    vitesse < 90 AND 
                    analyzed = 0
                ORDER BY timestamp_record DESC
        """
        
        # execute request sql
        cursor.execute(sql)
        # get result request
        all_car_event = cursor.fetchall()
        # close cursor
        cursor.close()
        
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
                            coords_item = (float(item[2]), float(item[3]))
                            coords_other = (float(other[2]), float(other[3]))
                            
                            # check the distance of the two cars events is lower than 500 meters
                            if geopy.distance.geodesic(coords_item, coords_other).m <= 500:
                                car_event.append(other)
                    
                    # check if there are at least 3 car events for create a traffic event (embouteillage)
                    if len(car_event) >= 3:
                        # create a traffic event (embouteillage)
                        create_traffic_event(database, "embouteillage", car_event[0][2], car_event[0][3], car_event[0][4], "cdc")
                        # update counter of traffic event created
                        nb_traffic_event_find += 1
                        # disable car events to avoid analyzing them a second time
                        for event in car_event:
                            set_car_event_analyzed(database, event[0])          
                    else:
                        # disable item car event to avoid analyzing it a second time
                        set_car_event_analyzed(database, item[0])
            
            logging.info(f"Data analysis completed.")
            logging.info(f"Number of traffic events created : {nb_traffic_event_find}")
        else:
            logging.info(f"No car events to analyse.")
        
        # close connection
        database.close()
        
        # sleep the processus
        time.sleep(10)


if __name__ == '__main__':
    analyse_data()
    
