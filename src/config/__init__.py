"""Project config package."""

from importlib.util import find_spec

if find_spec("pymysql") is not None:
    import pymysql

    pymysql.install_as_MySQLdb()
