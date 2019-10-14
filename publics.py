# -*- coding: UTF-8 -*-
import sys,time
sys.path.append('/root/dev/mail-sender')
sys.path.append('/root/dev/miz')
from datetime import datetime
import requests
db_name = 'miz2'
import inspect

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


def new_id(col):
    try:
        return col.find().sort(key_or_list='id', direction=-1).limit(1)[0]['id'] + 1
    except:
        PrintException()


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
    MESSAGE_SERVER_ADDRESS = 'http://logs.onmiz.org'
    SERVER_ADDRESS = 'https://server1.onmiz.org'
    MESSAGE_SERVER_PORT = '7070'
    SERVER_PORT = '6000'
    TEST_SERVER_PORT = '8000'
    SSL_SERVER_PORT = '8443'
    DB_NAME = 'miz'
    TEST_DB_NAME = 'tmiz'
    ODP_ROOT = SERVER_ADDRESS + '/miz/'
    LOG_SERVER = 'http://logs.onmiz.org:8080'
    MAIL_SERVER_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAxOC0xMC0yNyAxMjoyNDoxNC40MzMyOTEiLCJyb2xlIjoiYWRtaW4iLCJ1c2VyX2lkIjoiNWFjMzNiMGFjZjFlOGMyMzE2OTUwYzljIn0.yd5t5yaWYHV28y80QdHnU1QEjsqheRoVqObXehHpiQQ'
    MAIL_SERVER_IP = 'http://server1.onmiz.org:8585/'
    ODP_IMAGES = ODP_ROOT + 'images/'
    TEST_MODE = False
    MAX_HOME_BILLBOARD_COUNT = 5
    SPONSORED_DISTANCE = 7



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



def get_refcode():
    col_users = db()['users']
    code = random_str(6)
    while col_users.find_one({'ref_code': code}) != None:
        code = random_str(6)
    return code



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


def get_ref_code():
    import random, string
    from random import randint
    ref_code = ''.join(random.choice(string.uppercase) for i in range(2))
    ref_code += str(randint(1000, 9999))
    return ref_code


def random_digits():
    from random import randint
    return str(randint(1000, 9999))


def send_sms(text, number, date=datetime.now()):
    try:
        param_data = {
            'mobile': number,
            'text': text,
            'date': str(date)
        }
        requests.post(url='%s:%s/v1/sms' % (consts.MESSAGE_SERVER_ADDRESS, consts.MESSAGE_SERVER_PORT), json=param_data)
    except:
        PrintException()


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


def set_notification(user_id, text):
    from datetime import datetime
    col_sessions = db()['sessions']
    sessions = col_sessions.find({'user_id': user_id})
    notif_ids = []
    for session in sessions:
        notif_ids.append(session['notif_id'])

    if len(notif_ids) > 0:
        col_notifications = db()['notifications']
        col_notifications.insert({
            'text': text,
            'date': datetime.now(),
            'sent': False,
            'notif_ids': notif_ids
        })


def send_email_simple(to, title, body):
    import requests
    results = requests.post(url=consts.MAIL_SERVER_IP + 'mails', json={
        'token': consts.MAIL_SERVER_TOKEN,
        'to': to,
        'title': title,
        'body': body,
        'sent': False
    })


def send_registration_email(to, activation_code):
    try:
        f = open(consts.ROOT_DIR + '/templates/registration_email.html')
        email_content = f.read()
        email_content = email_content.replace('%activation_code%', activation_code)
        f.close()
        send_email_simple(to, "Activate your Miz account", email_content)
    except:
        PrintException()


def send_password_reset_email(to, activation_code):
    try:
        f = open(consts.ROOT_DIR + '/templates/registration_email.html')
        email_content = f.read()
        email_content = email_content.replace('%activation_code%', activation_code)
        f.close()
        send_email_simple(to, "Password reset code for Miz", email_content)
    except:
        PrintException()


def get_user_locale(user_id):
    # TODO: Think for a better solution
    from bson import ObjectId
    col_users = db()['users']
    user_info = col_users.find_one({'_id': ObjectId(user_id)})
    user_locale = 'fa'
    if user_info is not None:
        if 'user_locale' in user_info:
            user_locale = user_info['user_locale']
    return user_locale


def console(text):
    col_console = db()['console']
    col_console.insert({
        'url': inspect.stack()[0][3],
        'text': text,
        'create_date': datetime.now()

    })
