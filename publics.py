import sys
sys.path.append('/root/dev/app')
db_name = 'db_name'


def PrintException():
    import linecache
    import sys
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))
    # return 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)


def set_db(name):
    global db_name
    db_name = name


def set_test_mode(mode):
    consts.TEST_MODE = mode


def es():
    from elasticsearch import Elasticsearch
    return Elasticsearch('localhost')


def db():
    from pymongo import MongoClient
    con = MongoClient()
    return con[db_name]


def load_messages():
    messages = {}
    try:
        set_db(db_name)
        col_server_messages = db()['server_messages']
        for item in col_server_messages.find():
            group = item['group']
            name = item['name']
            if group not in messages: messages[group] = {}
            del item['group']
            del item['name']
            messages[group][name] = item
    except:
        PrintException()
    return messages


def load_notifications():
    notifications = {}
    try:
        set_db(db_name)
        col_server_notifications = db()['server_notifications']
        for item in col_server_notifications.find():
            group = item['group']
            name = item['name']
            if group not in notifications: notifications[group] = {}
            del item['_id']
            del item['group']
            del item['name']
            notifications[group][name] = item
    except:
        PrintException()
    return notifications


class consts:
    import os
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    page_size = 20
    MAX_TOKEN_DURATION = 1000000
    MESSAGES = load_messages()
    NOTIFICATIONS = load_notifications()
    CONSOLE_LOG = True
    LOG_ACTIVE = True
    PDP_ROOT = '/var/www/html/miz/'
    PDP_IMAGES = PDP_ROOT + 'images/'
    SERVER_ADDRESS = 'https://server1.onmiz.org'
    SERVER_PORT = '6000'
    DB_NAME = 'db_name'
    TEST_DB_NAME = 'tdb_name'
    ODP_ROOT = SERVER_ADDRESS + '/app/'
    LOG_SERVER = 'http://logs.onmiz.org:8080'
    ODP_IMAGES = ODP_ROOT + 'images/'
    TEST_MODE = False


def create_md5(str):
    import hashlib
    ps = hashlib.md5()
    ps.update(str)
    _hash = ps.hexdigest()
    ps = hashlib.sha1()
    ps.update(str)
    _hash += ps.hexdigest()[:18:-1]
    _hash = _hash[::-1]
    ps = hashlib.new('ripemd160')
    ps.update(_hash)
    return ps.hexdigest()[3:40]


def encode_token(data):
    import jwt
    import datetime
    data['date'] = str(datetime.datetime.now())
    return jwt.encode(data, 'ThisIsASecret@2019', algorithm='HS256')


def decode_token(token):
    import jwt
    try:
        result = jwt.decode(token, 'ThisIsASecret@2019', algorithms=['HS256'])
    except:
        result = None
        PrintException()
    return result


def random_str(length):
    import random, string
    return ''.join(random.choice(string.lowercase) for i in range(length))


def random_digits():
    from random import randint
    return str(randint(1000, 9999))


def log_status(l):
    from datetime import datetime
    col = db()['logs']
    del l['date']
    l['date'] = datetime.now()
    col.insert(l)


def prepare_item(item):

    if '_id' in item:
        item['id'] = str(item['_id'])
        del item['_id']
        for k, v in item.iteritems():
            if 'date' in k:
                item[k] = str(v)
    return item
