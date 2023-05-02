import sqlite3
import hashlib
from pathlib import Path


_DBNAME = Path('downloaded.sql')

_CREATE_TABLE = """\
create table downloaded_files (
    filename                text unique,
    path                    text unique,
    md5                     text
)
"""

_CHECK_FILE = """\
select count() from downloaded_files where filename="%s"
"""

_ADD_FILE = """\
insert into downloaded_files (filename, path, md5) values ("%s", "%s", "%s")
"""


class DB:
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self):
        self._db_conn = sqlite3.connect(_DBNAME, check_same_thread=False)
        try:
            self._db_conn.execute(_CREATE_TABLE)
            print('Created base.')
        except sqlite3.OperationalError:
            print('Base already exists.')

    def is_file_exists(self, filename: str):
        count, = self._db_conn.execute(_CHECK_FILE % filename).fetchone()
        assert count < 2
        return bool(count)

    def add_file(self, filename: str, filepath: str, md5: str):
        self._db_conn.execute(_ADD_FILE % (filename, filepath, md5))
        self._db_conn.commit()
