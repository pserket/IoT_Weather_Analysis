#!/usr/bin/python

import os
import sys
import json
from flask import Flask, request, jsonify

import pymysql
import requests
from datetime import datetime
from datetime import date
import cgi
import ast

# for telling the browser what is being outputted
print("Content-Type: text/html")
print("")
print("DSC190 API")

servername = "localhost"
username = "iotdev"
dbname = "iotdb"
password = "iotdb190"

# from https://stackoverflow.com/questions/1254454/fastest-way-to-convert-a-dicts-keys-values-from-unicode-to-str
def convert_keys_to_string(dictionary):
    """Recursively converts dictionary keys to strings."""
    if not isinstance(dictionary, dict):
        return dictionary
    return dict((str(k), convert_keys_to_string(v)) 
        for k, v in dictionary.items())

def execute_sql(sql, json_head = "", json_end = ""):

	connection = pymysql.connect(host=servername, user=username, password=password,
    	db=dbname, cursorclass= pymysql.cursors.DictCursor)

	try:
		with connection.cursor() as cursor:
			print(sql)
			num_rows = cursor.execute(sql)

			sys.stdout.write(json_head)
			first = True
			while num_rows > 0:
				if first == False:
					sys.stdout.write(",")
				result = cursor.fetchone()
				sys.stdout.write(str(convert_keys_to_string(result)))
				num_rows -= 1
				first = False

			sys.stdout.write(json_end)
	except pymysql.InternalError as error:
		print('error')
	finally:
		connection.commit()
		connection.close()
		print('success')
		return 'success'

def reg_helper(sql_query, json_head = "", json_end = ""):
	connection = pymysql.connect(host=servername, user=username, password=password,
        db=dbname, cursorclass= pymysql.cursors.DictCursor)

	ret_msg = "fail"
    try:
        with connection.cursor() as cursor:
            # print(sql)
            print("entered the function")
            num_rows = cursor.execute(sql_query)
            if num_rows > 0:
                ret_msg = 'success'
            # sys.stdout.write(json_head)
            first = True
            while num_rows > 0:
                # if first == False:
                #     sys.stdout.write(",")
                result = cursor.fetchone()
                # sys.stdout.write(str(convert_keys_to_string(result)))
                num_rows -= 1
                first = False
            # sys.stdout.write(json_end)
    except pymysql.InternalError as error:
        print('error')
    finally:
        connection.commit()
        connection.close()
        # print(ret_msg)
        return ret_msg	


# use with GET
arguments = cgi.FieldStorage()
if 'cmd' in arguments.keys():
	print(arguments['cmd'])
	print("this is extra new")
	if arguments['cmd'].value == 'LIST':
		json_head = "{\"devices\" : ["
		json_end = "]}"
		sql = "SELECT * FROM devices"
		
		if 'gid' in arguments.keys():
			gid = arguments['gid'].value
			sql = "SELECT * FROM devices WHERE groupID = " + str(gid)
		

		execute_sql(sql, json_head, json_end)

	elif arguments['cmd'].value == 'GROUPS':
		json_head = "{\"groups\" : ["
		json_end = "]}"
		sql = "SELECT * FROM groups ORDER BY groupID"

		if 'gid' in arguments.keys():
			gid = arguments['gid'].value
			sql = "SELECT * FROM groups WHERE groupID = " + str(gid)
		
		execute_sql(sql, json_head, json_end)

	elif (arguments['cmd'].value == 'REG') & arguments['mac'].value & arguments['gid'].value:
		print("entered elif")
		sys.stdout.write("elif entered")
		macToInsert = arguments['mac'].value
		gidToInsert = str(arguments['gid'].value)
		json_head = "{\"groups\" : ["
		json_end = "]}"
		sql = "UPDATE devices SET lastseen=NOW() WHERE mac='+macToInsert+' AND groupID='+gidToInsert+'"
		update_result = reg_helper(sql) # <---- THIS LINE
		if update_result == 'fail':
			sql = "INSERT INTO devices (groupID, mac, lastseen) VALUES (" + gidToInsert + "," + macToInsert + "," + "NOW())"
			execute_sql(sql, json_head, json_end)

	else:
		print('not a valid command')
		







