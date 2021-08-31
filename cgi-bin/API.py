#!/usr/bin/python
print("Content-type: text/html")
print("")

import os
import sys
import json
from flask import Flask, request, jsonify

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

def reg_helper(sql_query, json_head = "", json_end = ""):
    connection = pymysql.connect(host=servername, user=username, password=password,
        db=dbname, cursorclass= pymysql.cursors.DictCursor)
    ret_msg = "error"
    try:
        with connection.cursor() as cursor:
            num_rows = cursor.execute(sql_query)
            if num_rows > 0:
                ret_msg = 'success'
            else:
                ret_msg = 'fail'
            first = True
            while num_rows > 0:
                result = cursor.fetchone()
                num_rows -= 1
                first = False
    except:
        print(sys.exc_info())
    finally:
        connection.commit()
        connection.close()
        return ret_msg  


inputs = str(cgi.FieldStorage()).split("'")[-2]

inputs = inputs.replace('\\r','')
inputs = inputs.replace('\\n','')



arguments = json.loads(json.dumps(json.loads(inputs)))


# print(arguments)
if 'cmd' in arguments.keys():
    if arguments['cmd'] == 'LIST':
        json_head = "{\"devices\" : ["
        json_end = "]}"
        sql = "SELECT * FROM devices"
        if 'gid' in arguments.keys() and 'devmac' in arguments.keys():
            gid = arguments['gid']
            devmac = arguments['devmac']
            sql = "SELECT * FROM devices WHERE groupID = " + str(gid) +" AND mac='" + devmac+"'"
        elif 'gid' in arguments.keys():
            gid = arguments['gid']
            sql = "SELECT * FROM devices WHERE groupID = " + str(gid)
        execute_sql(sql, json_head, json_end)

    elif arguments['cmd'] == 'GROUPS':
        json_head = "{\"groups\" : ["
        json_end = "]}"
        sql = "SELECT * FROM groups ORDER BY groupID"
        if 'gid' in arguments.keys():
            gid = arguments['gid']
            sql = "SELECT * FROM groups WHERE groupID = " + str(gid)
        execute_sql(sql, json_head, json_end)

    elif (arguments['cmd'] == 'REG') and arguments['mac'] and arguments['gid'] and arguments['ip']:
        macToInsert = arguments['mac']
        gidToInsert = arguments['gid']
        ipToInsert = arguments['ip']

        json_head = "{\"REG\" : ["
        json_end = "]}"
        sql = "UPDATE devices SET lastseen=NOW() WHERE mac='"+macToInsert+"' AND groupID="+gidToInsert+" AND ip='"+ipToInsert+"'"
        update_result = reg_helper(sql) 
        # if update_result == 'fail':
        #   sql = "INSERT INTO devices (groupID, mac, ip, lastseen) VALUES (" + gidToInsert + ",'" + macToInsert + "','" + ipToInsert + "'," + "NOW())"
        #   print("SQL Executed: " + sql)
        #   execute_sql(sql, json_head, json_end)
        # else:
        #   print("SQL Executed: " + sql)
        sql = "SELECT lastseen, mac FROM devices WHERE mac= '" + arguments['mac'] + "'"
        
        json_head = "{\"devices\" : ["
        json_end = "]}"
        returnStatus = True
        execute_sql(sql, json_head, json_end, returnStatus)
        
    elif (arguments['cmd'] == "LOG") and arguments['devmac'] and arguments['gid'] and arguments['BLEInfo']:
        devmacToInsert = arguments['devmac']
        gidToInsert = arguments['gid']
        already_inserted = [] # ignore duplicates from same polling cycle
        sql = "INSERT INTO blelogs (gid, devmac, blemac, blerssi, timestamp) VALUES"
        first = True
        for ble in arguments['BLEInfo']['beacons']:
            macToInsert = ble['mac']
            rssiToInsert = ble['rssi']
            if macToInsert in already_inserted:
                continue
            else:
                already_inserted.append(macToInsert)
                if first:
                    sql = sql + " ("+gidToInsert  + ", '"+devmacToInsert +"','"+macToInsert +"', "+ rssiToInsert +", NOW())"
                    first = False
                else:
                    sql = sql + ", ("+gidToInsert  + ", '"+devmacToInsert +"','"+macToInsert +"', "+ rssiToInsert +", NOW())"

        print("SQL Executed: " + sql)
        execute_sql(sql)
        returnStatus=True
        json_head = "{\"LOG\" : ["
        json_end = "]}"
    elif arguments['cmd'] == "VIEWBLE":
        if 'gid' in arguments.keys() and 'devmac' in arguments.keys() and 'limit' in arguments.keys():
            gidToInsert = arguments['gid']
            macToInsert = arguments['devmac']
            resLimit = str(arguments['limit'])
            sql = "SELECT * FROM blelogs WHERE gid="+str(gidToInsert)+" AND devmac='"+macToInsert+"' ORDER BY timestamp DESC LIMIT "+resLimit
            execute_sql(sql)
        elif 'gid' in arguments.keys() and 'limit' in arguments.keys():
            
            gidToInsert = arguments['gid']
            
            resLimit = str(arguments['limit'])
            
            sql = "SELECT * FROM blelogs WHERE gid=" +str(gidToInsert)+ " ORDER BY timestamp DESC LIMIT "+resLimit
            
            execute_sql(sql)
        else:
            sql = "SELECT * FROM blelogs ORDER BY timestamp DESC LIMIT 5"
            execute_sql(sql)
    elif arguments['cmd'] == "LOGCLIMATE" and arguments['temp'] and arguments['hum'] and arguments['mac']:
        humToInsert = arguments['hum']
        tempToInsert = arguments['temp']
        if type(arguments['hum']) != float:
            humToInsert = "NULL"
        if type(arguments['temp']) != float:
            tempToInsert = "NULL"
        sql = "INSERT INTO mcdata (gid,timerstamp, temp, hum, mac) VALUES (5, NOW(),"+str(tempToInsert)+","+str(humToInsert)+",'"+arguments['mac']+"')"
        # print(sql)
        execute_sql(sql)
        test_sql = "SELECT * FROM mcdata WHERE gid=5"
        execute_sql(test_sql)
    elif arguments['cmd'] == "VIEWCLIMATE" and arguments['gid'] and arguments['mac']:
        sql = "SELECT * FROM mcdata WHERE gid="+str(arguments['gid'])+" AND mac='"+arguments['mac'] + "'"
        execute_sql(sql)
    elif arguments['cmd'] == "CLIMATESTATS" and arguments['gid'] and arguments['mac']:
        gidToInsert = arguments['gid']
        macToInsert = arguments['mac']
        sql = "SELECT temp, hum, substring(timerstamp, 12, 5) AS min FROM mcdata WHERE timerstamp > DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND gid="+gidToInsert+" AND mac='"+macToInsert+"'"
        execute_sql(sql)
    elif arguments['cmd'] == "FORECAST" and arguments['lat'] and arguments['lon']:
        response = requests.get("http://api.openweathermap.org/data/2.5/weather?lon="+str(arguments['lon'])+"&lat="+str(arguments['lat'])+"&appid=0354c29c5e773c46d37727c8a0455d58")
        data = json.loads(json.dumps(json.loads(response.content)))
        weatherData = data["main"]
        temp = weatherData['temp'] - 273.15
        minTemp = weatherData['temp_min'] - 273.15
        maxTemp = weatherData['temp_max'] - 273.15
        feelslike = weatherData['feels_like'] - 273.15
        hum = weatherData['humidity']
        sys.stdout.write(str({"temp":temp, "minTemp":minTemp, "maxTemp":maxTemp, "feelslike":feelslike, "hum":hum}))

    elif arguments['cmd'] == "INSIDEOUT" and arguments['mac1'] and arguments['mac2'] and arguments['gid']:
        # sql = "SELECT temp, mac, timerstamp FROM mcdata WHERE gid="+str(arguments['gid'])+" AND timerstamp > '2020-06-02 22:00:00'"
        sql = "SELECT foreTemp, temp, mac, timerstamp\
                FROM (\
                SELECT \
                    DAYOFYEAR(timestamp) Day,\
                    HOUR(timestamp) Hour,\
                    temp as foreTemp,\
                    hum as foreHum\
                FROM forecast WHERE gid=05) as F1\
                RIGHT JOIN (\
                SELECT\
                    DAYOFYEAR(timerstamp) Day,\
                    HOUR(timerstamp) Hour,\
                    timerstamp,\
                    temp,\
                    hum,\
                    mac\
                FROM mcdata\
                WHERE gid=05\
                AND timerstamp > '2020-06-02 22:00:00'\
                ) AS F2\
                ON F1.DAY = F2.Day \
                AND F1.HOUR = F2.HOUR"
        execute_sql(sql)

    elif arguments['cmd'] == "INSIDEOUTHUM" and arguments['mac1'] and arguments['mac2'] and arguments['gid']:
        # sql = "SELECT hum, mac, timerstamp FROM mcdata WHERE gid="+str(arguments['gid'])+" AND timerstamp > '2020-06-02 22:00:00'"
        sql = "SELECT foreHum, hum, mac, timerstamp\
        FROM (\
        SELECT \
            DAYOFYEAR(timestamp) Day,\
            HOUR(timestamp) Hour,\
            temp as foreTemp,\
            hum as foreHum\
        FROM forecast WHERE gid=05) as F1\
        RIGHT JOIN (\
        SELECT\
            DAYOFYEAR(timerstamp) Day,\
            HOUR(timerstamp) Hour,\
            timerstamp,\
            temp,\
            hum,\
            mac\
        FROM mcdata\
        WHERE gid=05\
        AND timerstamp > '2020-06-02 22:00:00'\
        ) AS F2\
        ON F1.DAY = F2.Day \
        AND F1.HOUR = F2.HOUR"
        execute_sql(sql)

    elif arguments['cmd'] == "STATS":
        # pete - retrieve the number of distinct blemacs per hour
        sql = "SELECT count_ble_3C, count_ble_8C, first_table.dayhour FROM \
(SELECT *, CONCAT(day,hour) as dayhour \
FROM (select COUNT(DISTINCT blemac) as count_ble_3C, substring(timestamp, 12, 2) as hour, \
substring(timestamp, 9, 2) as day \
from iotdb.blelogs where gid=5 AND devmac='CC:50:E3:A8:EB:3C' group by hour,  day order by day, hour) as counts_over_time1 \
WHERE DAY >= 15) as first_table \
INNER JOIN \
(SELECT *, CONCAT(day,hour) as dayhour FROM (select COUNT(DISTINCT blemac) as count_ble_8C, substring(timestamp, 12, 2) as hour, \
substring(timestamp, 9, 2) as day \
from iotdb.blelogs where gid=5 AND devmac='CC:50:E3:B0:21:8C' group by hour,  day order by day, hour) as counts_over_time2 \
WHERE DAY >= 15) as second_table ON first_table.dayhour=second_table.dayhour"
        execute_sql(sql)
    
    else:
        print('not a valid command')
        

