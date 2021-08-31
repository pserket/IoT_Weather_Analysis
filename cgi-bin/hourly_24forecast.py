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
from datetime import datetime
from datetime import date
import cgi
#import ast


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


# specify the unix datetime we want hourly forecast for
dt = 1591401600

response = requests.get("http://api.openweathermap.org/data/2.5/onecall/timemachine?units=metric&lat=32.86&lon=-117.21&dt="+str(dt)+"&appid=0354c29c5e773c46d37727c8a0455d58")
#print(response.content)

data = json.loads(json.dumps(json.loads(response.content)))
# print(data["hourly"] # a list of the weather for 24 hour period starting at the dt
print(data["hourly"][0])
# print(type(data))
# print(data["main"])

valsToInsert = []
first = True
for forecast in data["hourly"]:
    temp = forecast["temp"]
    timestamp = forecast["dt"] - 7*60*60 # convert UTC to PST
    hum = forecast["humidity"]
    timestamp = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    if first:
        valsToInsert.append("(5, " + str(temp) + ", " + str(hum)+ ", '"+timestamp+"', " + "'Hourly Open Weather Celsius')")
    else:
        valsToInsert.append(" ,(5, " + str(temp) + ", " + str(hum)+ ", '"+timestamp+"', " + "'Hourly Open Weather Celsius')")
    first = False


sql = "INSERT INTO forecast (gid, temp, hum, timestamp, provider) VALUES " + "".join(valsToInsert)
print(sql)
status = execute_sql(sql)
print(status)


# weatherData = data["main"]

# temp = weatherData['temp']
# minTemp = weatherData['temp_min']
# maxTemp = weatherData['temp_max']
# hum = weatherData['humidity']

# print(str(temp))
# valsToInsert = "5, " + str(temp) + ", " + str(minTemp)  + ", " + str(max_temp)  + ", " + str(hum)  + ", NOW(), " + "Hourly Open Weather Celsius"
# sql = "INSERT INTO forecast (gid, temp, min_temp, max_temp, hum, timestamp, provider) VALUES ( " + valsToInsert +")"
# print(sql)


# inputs = str(cgi.FieldStorage()).split("'")[-2]

# inputs = inputs.replace('\\r','')
# inputs = inputs.replace('\\n','')


# arguments = json.loads(json.dumps(json.loads(inputs)))


# # print(arguments)
# if 'cmd' in arguments.keys():

