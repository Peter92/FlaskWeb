from __future__ import absolute_import

import pymysql
    

class DatabaseConnection(object):
    """Wrapper for easy MySQL queries.

    Common Parameters:
        table (str): Table name to query
        
        values [insert/update] (dict): Set what values to assign to columns.
            {'column1': 'value1', 'column2': 57}
            
        values [read] (list): Choose the columns to get results for.
            ['column1', 'column2']
            
        where (str): Limit the results.
            'ID = 5 AND Updated < UNIX_TIMESTAMP()'
            
        order (list): What to order the results by.
            ['Email DESC', 'ID ASC']

        limit (int): Limit the results.

        offset (int): How many records to skip.
    """

    def __init__(self, host, database, user, password):
        
        #port 3306 charset utf8 use_unicode True
        self.connection = pymysql.connect(host=host, db=database, user=user, password=password)
        self.cursor = self.connection.cursor()
    
    def insert_record(self, table, values):
        """White a line to the database.

        INSERT INTO `table` (key1, key2, key3) VALUES (%s, %s, %s)
        """
        
        sql = 'INSERT INTO {}'.format(table)
        columns = sorted(values.keys())
        sql += ' ({}) VALUES ({})'.format(', '.join(i for i in columns),
                                          ', '.join('%s' for i in columns))
        
        num_records = self.cursor.execute(sql, [values[i] for i in columns])
        self.connection.commit()
        return self.cursor.lastrowid


    def count_records(self, table, where=''):
        """SELECT count(*) AS _C as _RowCount FROM table WHERE x = y"""
        result = self.get_records(table, values=['count(*)'], where=where)
        return result[0][0]


    def get_records(self, table, values, where='', order='', limit=None, offset=0):
        """Return records from query."""
        sql = 'SELECT {} FROM `{}`'.format(', '.join(values), table)
        if where:
            sql += ' WHERE {}'.format(where.strip())
        if order:
            sql += ' ORDER BY {}'.format(', '.join(order))
        if limit is not None:
            sql += ' LIMIT {}'.format(int(limit))
        if offset:
            sql += ' OFFSET {}'.format(offset)
        num_records = self.cursor.execute(sql)
        return self.cursor.fetchall()

        
    def update_records(self, table, values, where=''):
        """UPDATE table SET x = y WHERE a = b AND b < 3"""
        sql = 'UPDATE {} SET '.format(table)
        header_list = sorted(values.keys())
        value_list = [values[header] for header in header_list]
        sql += '{} = %s'.format(' = %s, '.join(header_list))
        if where:
            sql += ' WHERE {}'.format(where.strip())
        num_records = self.cursor.execute(sql, value_list)
        self.connection.commit()
        return num_records

    
    def sql(self, sql, *args):
        num_records = self.cursor.execute(sql, args)
        self.connection.commit()
        if sql.startswith('SELECT count(*) FROM'):
            return self.cursor.fetchall()[0][0]
        if sql.startswith('SELECT'):
            return self.cursor.fetchall()
        elif sql.startswith('UPDATE'):
            return num_records
        elif sql.startswith('INSERT'):
            return self.cursor.lastrowid
        elif sql.startswith('DELETE'):
            return num_records
