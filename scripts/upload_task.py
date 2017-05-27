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

GLOBAL_PATH = '/data/niuxl/lavaFace'

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
            return None
        self.queue.put(conn, 1)

    def clear(self):
        while self.queue.size():
            conn = self.queue.get(1)
            conn.close()
        return None

def main():
    while True:
        diyMySQL=DiyMysql(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB)
        if not diyMySQL.connect():
            time.sleep(3)
            continue

        diyMySQL.query("SELECT ti.id, data_path, task_flag, model_url, model_key, model_headers FROM task_info ti, deepface_model dm WHERE ti.task_model_id = dm.id AND task_status_id = 2")
        for record in diyMySQL.fetchAll():
            task_id = record[0]
            model_url = record[3]
            model_key = record[4]
            model_headers = record[5]

            task_path = GLOBAL_PATH + record[1]
            json_data = json.loads(open(task_path).read())
            for facetrack in json_data["facetracks"]:
                imgs = []
                for image in facetrack["facetrack_images"]:
                    image_path = '/data/niuxl/lavaFace/' + image['imgpath']
                    base64_blob = base64.b64encode(open(image_path).read())
                    imgs.append(base64_blob)

                payload = {
                    "id": 1,
                    "jsonrpc": "2.0",
                    "method": "createfacetrack",
                    "params": {
                        "appkey": model_key,
                        "imgs": imgs
                    }
                }

                response = requests.post(model_url, data=json.dumps(payload), headers=json.loads(model_headers)).json()
                if response['result']['code'] == 0:
                    affected_rows = diyMySQL.query(
                        "INSERT INTO facetrack(`facetrack_id`, `image_path`, `descriptor`, `tracking_time`, `src_id`, `image_num`, `task_id`, `created_time`, `isdeleted`, `isnewlycreated`, `person_id`) " \
                        "VALUES(%s, %s, %s, %s, %s, %s, %s, now(), 0, 0, '')", 
                        (response['result']['results']['id_facetrack'],
                        facetrack['big_image'],
                        facetrack['descriptor'],
                        facetrack['tracking_time'],
                        facetrack['src_id'],
                        len(imgs),
                        task_id)
                    )

                    affected_rows = diyMySQL.query('SELECT last_insert_id()')
                    for record in diyMySQL.fetchAll():
                        last_insert_id = record[0]

                    for img in imgs:
                        affected_rows = diyMySQL.query(
                            'INSERT INTO facetrack_image(`facetrack_id`, `img_base64`, `img_id`, `created_time`, `isdeleted`) ' \
                            'VALUES(%s, %s, %s, now(), 0)', 
                            (last_insert_id,
                            img,
                            str(uuid.uuid1()))
                        )

                    diyMySQL.commit()

            affected_rows = diyMySQL.query("UPDATE task_info SET task_status_id = 3 WHERE id = %s", [task_id])
            diyMySQL.commit()

        diyMySQL.close()
        print('Sleep for 5 seconds...')
        time.sleep(5)

if __name__ == '__main__':
    main()

