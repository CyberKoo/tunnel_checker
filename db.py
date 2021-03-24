import os
import sqlite3
from pathlib import Path

_connection = None


def _connection_check(func):
    def wrapper(*args, **kwargs):
        if _connection is None:
            raise Exception('database is not initialized')
        return func(*args, **kwargs)

    return wrapper


def init(db_path):
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(db_path)
        base = os.path.dirname(db_path)
        with Path(base, 'init.sql') as sql_script:
            if sql_script.exists():
                with open(sql_script) as sql:
                    cursor = _connection.cursor()
                    cursor.executescript(sql.read())


@_connection_check
def query(sql, param=None):
    cursor = _connection.cursor()
    if param is None:
        return cursor.execute(sql)
    else:
        return cursor.execute(sql, param)


@_connection_check
def commit():
    _connection.commit()


@_connection_check
def close():
    _connection.close()
