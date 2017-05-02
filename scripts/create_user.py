##################################################################################
#
# @All Right Reserved (C), 2014
# Filename:	__global_mysql.py
# Version:	ver1.0
# Author:	TERRY-V
# Support:	http://blog.sina.com.cn/terrynotes
# Date:		2014/05/22
#
##################################################################################

#!/usr/bin/env python

import os
import sys

import MySQLdb
import _mysql_exceptions as DB_EXC
import Queue

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
    diyMySQL=DiyMysql(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB)
    if not diyMySQL.connect():
        return

    for i in range(2, 100):
        username = 'yunshitu%04d' % i
        print(username)
        diyMySQL.query("INSERT INTO usercenter_user(password, is_superuser, username, first_name, last_name, email, img, intro, is_staff, is_active, date_joined) VALUES('pbkdf2_sha256$30000$2d2GsoqOM3ta$NkBXy7fszAueP1KJLq7ahSGQJ4klsgU9KiMh07Bds4Y=', 0, '%s', '', '', 'xxx@yunshitu.cn', '/static/avatar/default.gif', '', 0, 1, now())" % username)
    
    diyMySQL.commit()
    diyMySQL.close()

if __name__ == '__main__':
	main()

