
from db import MySQLdb


mysqlConfig = {
            "host": "127.0.0.1",
            "port": 3306,
            "user": "root",
            "password": "168mysql",
            "database": "pickfish",
            "maxConnections": 55,
            "minFreeConnections": 11
        }

#mysqlConfig = {
#            "host": "192.168.16.50",
#            "port": 3306,
#            "user": "user",
#            "password": "a123456",
#            "database": "pickfish",
#            "maxConnections": 55,
#            "minFreeConnections": 11
#        }

mysql = MySQLdb(mysqlConfig)