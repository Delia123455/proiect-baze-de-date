import mysql.connector
from mysql.connector import errorcode

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port=3006,
            user="root",
            password="cristianAZ06!",
            database="centru_medical"
        )
        return conn
    except mysql.connector.Error as err:
        print("Eroare!!!: ", err)
        return None
