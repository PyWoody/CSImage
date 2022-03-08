import hashlib, os, sqlite3

from multiprocessing import Pool


def process(cwd, img_types=None):
    """Iterator that yields a tuple of (bool, filpath) if the image found
    was unique or not.
    """
    if img_types is None:
        img_types = {
            '.jpg', '.jpeg', '.tiff', '.gif', '.png', '.psd', '.eps', '.raw'
        }
    con, cur = setup_db()
    crawler = crawl(cwd, img_types)
    with Pool() as pool:
        for result in pool.imap_unordered(generate_hash, crawler, 10):
            fpath, img_hash = result
            cur.execute(
                'SELECT * FROM file_hashes WHERE hash = (?)', (img_hash,)
            )
            unique = False if cur.fetchone() else True
            if unique:
                cur.execute(
                    'INSERT INTO file_hashes (fpath, hash) VALUES (?, ?)',
                    (fpath, img_hash)
                )
                con.commit()
            yield unique, fpath

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

    Required:
        fpath (arg): A filepath or a PathLike object
    """
    f_hash = hashlib.md5()
    with open(fpath, 'rb') as f:
        while chunk := f.read(8192):
            f_hash.update(chunk)
    return fpath, f_hash.digest()

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

