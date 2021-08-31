#!/usr/bin/python
print("Content-type: text/html")
print("")

import os
import sys
import json
from flask import Flask, request, jsonify
import time

import pymysql
import requests
from datetime import datetime, date
import cgi


servername = "localhost"
username = "iotdev"
dbname = "iotdb"
password = "iotdb190"


def convert_keys_to_string(dictionary):
    """Recursively converts dictionary keys to strings."""
    if not isinstance(dictionary, dict):
        return dictionary
    return dict((str(k), convert_keys_to_string(v)) 
        for k, v in dictionary.items())

def execute_sql(sql, json_head = "", json_end = "", returnStatus=False):
    connection = pymysql.connect(host=servername, user=username, password=password,
        db=dbname, cursorclass= pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            num_rows = cursor.execute(sql)
            sys.stdout.write(json_head)
            first = True
            if (num_rows == 1) & returnStatus:
                result = cursor.fetchone()
                result['status'] = 'OK'
                sys.stdout.write(str(convert_keys_to_string(result)))
                num_rows -= 1
                first = False
            while num_rows > 0:
                if first == False:
                    sys.stdout.write(",")
                result = cursor.fetchone()
                if "INSERT" in sql:
                    num_rows -= 1
                    first = False
                    continue
                sys.stdout.write(str(convert_keys_to_string(result)))
                num_rows -= 1
                first = False
            sys.stdout.write(json_end)
    except:
        print(sys.exc_info())
    finally:
        connection.commit()
        connection.close()
        return 'success'


# time.sleep(timeout)

timeout = 3600

while True:
    response = requests.get("http://api.openweathermap.org/data/2.5/weather?zip=92122&units=metric&appid=0354c29c5e773c46d37727c8a0455d58")

    data = json.loads(json.dumps(json.loads(response.content)))

    print(data['main'])


    temp = data['main']["temp"]
    hum = data['main']["humidity"]


    valsToInsert = ("(5, " + str(temp) + ", " + str(hum)+ ", NOW(), " + "'Hourly Open Weather Celsius')")
    print(valsToInsert)
    sql = "INSERT INTO forecast (gid, temp, hum, timestamp, provider) VALUES " + valsToInsert
    print(sql)
    status = execute_sql(sql)
    print(status)
    time.sleep(timeout)