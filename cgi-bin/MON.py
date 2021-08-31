#!/usr/bin/python
print("Content-type: text/html")
print("")

# code to check and update status of esp32 device from sql table

import time
import os
import sys
import json
from flask import Flask, request, jsonify

import pymysql
import requests
from datetime import datetime
from datetime import date
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


while True:
	# check and update status of device
	# CHANGE STATUS TO TIMEOUT IF DEVICE NOT SEEN AFTER 30 SECONDS
	sql_TIMEOUT = "UPDATE devices SET status = 'TIMEOUT' WHERE NOW() > DATE_ADD(lastseen, INTERVAL 300 SECOND) AND groupID=5"
	execute_sql(sql_TIMEOUT)
	time.sleep(1)
	# CHANGE STATUS TO ERROR IF DEVICE NOT SEEN AFTER 60 SECONDS
	sql_ERR = "UPDATE devices SET status = 'ERROR' WHERE NOW() > DATE_ADD(lastseen, INTERVAL 600 SECOND) AND groupID=5"
	execute_sql(sql_ERR)
	time.sleep(1)
	# CHANGE STATUS TO WARNING IF DEVICE RESUMES AFTER 15 SECONDS FROM TIMEOUT OR ERROR
	sql_WARN = "UPDATE devices SET status = 'WARNING' WHERE (status = 'TIMEOUT' OR status = 'ERROR') AND NOW() < DATE_ADD(lastseen, INTERVAL 120 SECOND) AND groupID=5"
	execute_sql(sql_WARN)
	time.sleep(1)
	# CHANGE STATUS TO OK IF DEVICE RESUMES BEFORE 30 SECONDS
	sql_OK = "UPDATE devices SET status = 'OK' WHERE status IN ('TIMEOUT', 'ERROR') AND NOW() <= DATE_ADD(lastseen, INTERVAL 120 SECOND) AND groupID=5"
	execute_sql(sql_OK)
	
	time.sleep(5)

connection.close()