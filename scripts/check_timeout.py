# -*- coding: utf-8 -*-

#!/usr/bin/env python

import base64
import os
import json
import urllib2
import uuid
import datetime
import requests
import sys
import time

import MySQLdb
import _mysql_exceptions as DB_EXC
import Queue

reload(sys)  
sys.setdefaultencoding('utf8')

MYSQL_HOST = '192.168.1.123'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'yunshitu1!'
MYSQL_DB = 'LavaFace'

class DiyMysql(object):
	def __init__(self, host, user, passwd, dbName):
		self.host = host
		self.user = user
		self.passwd = passwd
		self.dbName = dbName
		self.cxn = None
		self.cur = None

	def connect(self):
		try:
			self.cxn = MySQLdb.connect(self.host, self.user, self.passwd, self.dbName, charset = 'utf8',port =  3306)
			if not self.cxn:
				print 'MySQL server connect failed...'
				return False
			self.cur = self.cxn.cursor()
			return True
		except Exception as e:
			return False

	def getCursor(self):
		return self.cur

	def commit(self):
		return self.cxn.commit()

	def rollback(self):
		return self.cxn.rollback()

	def close(self):
		self.cur.close()
		self.cxn.close()

	def query(self, sql, args=None, many=False):
		affected_rows = 0
		if not many:
			if args == None:
				affected_rows = self.cur.execute(sql)
			else:
				affected_rows = self.cur.execute(sql, args)
		else:
			if args==None:
				affected_rows = self.cur.executemany(sql)
			else:
				affected_rows = self.cur.executemany(sql, args)
		return affected_rows


	def fetchAll(self):
		return self.cur.fetchall()

class ConnectPool(object):
    def __init__(self, num):
        self.num = num
        self.queue = Queue.Queue(self.num)
        for i in range(num):
			self.createConnection()

    def get(self):
        if not self.queue.qsize():
            self.createConnection()
        return self.queue.get(1)

    def free(self, conn):
        self.queue.put(conn, 1)

    def createConnection(self):
        conn = DiyMysql(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB)
        if not conn.connect():
            print 'connect to mysql error'
            return
        self.queue.put(conn, 1)

	def clear(self):
		while self.queue.size():
			conn = self.queue.get(1)
			conn.close()
		return

def main():
    while True:
        diyMySQL=DiyMysql(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB)
        if not diyMySQL.connect():
            time.sleep(10)
            continue

        diyMySQL.query("SELECT facetrack_id FROM LavaFace.facetrack WHERE unix_timestamp(now()) - unix_timestamp(allocated_time) >= 180 and status = 1")
        for data in diyMySQL.fetchAll():
            print('Checked ', data[0], ' timeout...')
            affected_rows = diyMySQL.query("UPDATE facetrack SET user_id = null, status = null, allocated_time = null WHERE facetrack_id = %s", [data[0]])
        diyMySQL.commit()

        diyMySQL.close()
        time.sleep(10)

if __name__ == '__main__':
	main()

