#!/usr/bin/python
#coding=utf-8
# -*- coding: utf-8 -*- 
import sys 
reload(sys) 
sys.setdefaultencoding('utf-8') 

import MySQLdb.cursors
import MySQLdb
import json
import re

from decimal import Decimal

from pprint import pprint
import pymongo
import random
import time


class mongo_crud():
    def __init__(self):
        self.mongo_conn  = pymongo.MongoClient("mongodb://192.168.1.62:28881" )
        self.mongo_db    = self.mongo_conn.qilong_logs

        #用户认证
        self.mongo_db.authenticate("qilong","qilong")

        print self.mongo_db.profiling_info
        print self.mongo_db.name

    def get_crud(self,collection):
        self.mongo_collection=eval("self.mongo_db.%s"%(collection))
        return self.mongo_collection


    #打印所有数据
    def show_table(self,table,fields):
        data2 = eval("self.mongo_db.%s.find({},%s)"%(table,fields))
        for i in data2:
            print i['pid']

    def __del__(self):
        self.mongo_conn.close();

