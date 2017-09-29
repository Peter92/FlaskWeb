from __future__ import absolute_import

import pymysql


class DatabaseConnection(object):

    def __init__(self, host, database, user, password):
        
        #Not in use (but not sure if needed) - port: 3306, charset: utf8, use_unicode: True
        self.connection = pymysql.connect(host=host, db=database, user=user, password=password)
        self.cursor = self.connection.cursor()
        
    def sql(self, sql, *args):
        num_records = self.cursor.execute(sql, args)
        self.connection.commit()
        if sql.startswith('SELECT count(*) FROM'):
            return self.cursor.fetchall()[0][0]
        elif sql.startswith('SELECT'):
            return self.cursor.fetchall()
        elif sql.startswith('UPDATE'):
            return num_records
        elif sql.startswith('INSERT'):
            return self.cursor.lastrowid
        elif sql.startswith('DELETE'):
            return num_records
