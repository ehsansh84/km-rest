import sys, os
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


def ExceptionLine():
    import linecache
    import sys
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    return f"{filename}:{lineno} => {line.strip()}"


def set_db(name):
    global db_name
    db_name = name


def set_test_mode(mode):
    consts.TEST_MODE = mode


def es():
    from elasticsearch import Elasticsearch
    return Elasticsearch('localhost')


def db():
    try:
        from pymongo import MongoClient
        MONGO_CONNECTION = os.getenv('MONGO')
        con = MongoClient('mongodb://' + MONGO_CONNECTION)
        return con[db_name]
    except:
        PrintException()
    return None


def load_messages():
    messages = {}
    try:
        import json
        f = open('strings/messages.json', 'r')
        for item in json.loads(f.read()):
            group = item['group']
            name = item['name']
            if group not in messages: messages[group] = {}
            del item['group']
            del item['name']
            messages[group][name] = item
    except:
        PrintException()
    return messages


def create_md5(s, encoding='utf-8'):
    from hashlib import md5
    return md5(s.encode(encoding)).hexdigest()


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
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(10))


def log_status(l):
    from datetime import datetime
    col = db()['logs']
    del l['date']
    l['date'] = datetime.now()
    col.insert(l)
