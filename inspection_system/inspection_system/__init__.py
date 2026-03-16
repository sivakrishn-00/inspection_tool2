import pymysql

pymysql.install_as_MySQLdb()

import MySQLdb
if not hasattr(MySQLdb, 'version_info'):
    MySQLdb.version_info = (2, 2, 1, 'final', 0)
MySQLdb.version_info = (2, 2, 1, 'final', 0)
