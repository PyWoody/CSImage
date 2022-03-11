import hashlib
import os
import sqlite3
import zlib

from multiprocessing import Pool
from queue import Queue


class ImageQueue(Queue):

    SENTINEL = object()

    def __iter__(self):
        while True:
            try:
                task = self.get()
                if task is self.SENTINEL:
                    return
                yield task
            finally:
                self.task_done()

    def close(self):
        self.put(self.SENTINEL)


def process(cwd, img_types=None):
    """Iterator that yields a tuple of (bool, filpath) if the image found
    was unique or not.
    """
    if img_types is None:
        img_types = { '.jpg', '.jpeg', '.tiff', '.gif', '.png'}
    con, cur = setup_db()
    crawler = crawl(cwd, img_types)
    with Pool() as pool:
        for fpath, hash_result, mem in pool.imap_unordered(generate_hash, crawler, 10):
            if isinstance(hash_result, Exception):
                yield False, fpath, zlib.compress(b'')  # Log
            else:
                cur.execute(
                    'SELECT * FROM file_hashes WHERE hash = (?);', (hash_result,)
                )
                exists = True if cur.fetchone() else False
                if not exists:
                    cur.execute(
                        'INSERT INTO file_hashes (hash) VALUES (?);',
                        (hash_result,)
                    )
                    con.commit()
                yield exists, fpath, mem
    con.close()

def crawl(cwd, img_types):
    """Iterator that yields the filepath of a file that is found
    in img_types
    """
    for root, dirs, files in os.walk(cwd):
        for f in files:
            if os.path.splitext(f)[1].lower() in img_types:
                yield os.path.join(root, f)

def generate_hash(fpath):
    """Returns a tuple of the filepath and an MD5 hash for the specified file
    or an Exception

    Required:
        fpath (arg): A filepath or a PathLike object
    """
    try:
        mem_bytes = b''
        f_hash = hashlib.md5()
        with open(fpath, 'rb') as f:
            while chunk := f.read(8192):
                f_hash.update(chunk)
                mem_bytes += chunk
    except Exception as e:
        return fpath, e, b''
    else:
        return fpath, f_hash.digest(), zlib.compress(mem_bytes, level=9)

def setup_db():
    """Creates an in-memory SQLite DB.

    returns a tuple of (connection (con), cursor (cur))
    """
    con = sqlite3.connect(':memory:')
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE file_hashes( 
            fpath TEXT NOT NULL,
            hash TEXT NOT NULL
        );
        '''
    )
    cur.execute('CREATE UNIQUE INDEX hash_index ON file_hashes(hash);')
    con.commit()
    return con, cur

