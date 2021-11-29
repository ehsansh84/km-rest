import sys
sys.path.append('/app')
from publics import db, create_md5, set_db
from consts import consts
set_db(consts.DB_NAME)


def insert_users():
    col_users = db()['users']
    if col_users.count_documents({'username': 'admin'}) == 0:
        col_users.insert_one({
            'name': 'ehsan',
            'family': 'shirzadi',
            'username': 'admin',
            'password': create_md5('1'),
            'role': 'admin',
        })


def insert_messages():
    col_server_messages = db()['server_messages']
    col_server_messages.drop()
    col_server_messages.insert_many([
        {
            'group': 'user',
            'name': 'token_not_received',
            'code': 401,
            'status': False,
            'en': 'Token not received'
        },
        {
            'group': 'user',
            'name': 'token_validated',
            'code': 200,
            'status': True,
            'en': 'Token validated'
        },
        {
            'group': 'user',
            'name': 'user_not_exists',
            'code': 401,
            'status': False,
            'en': 'User not exists'
        },
        {
            'group': 'user',
            'name': 'token_expired',
            'code': 401,
            'status': False,
            'en': ''
        },
        {
            'group': 'user',
            'name': 'access_denied',
            'code': 401,
            'status': False,
            'en': 'Access denied'
        },
        {
            'group': 'user',
            'name': 'permission_not_defined',
            'code': 401,
            'status': False,
            'en': 'Permission not defined'
        },
        {
            'group': 'user',
            'name': 'method_not_specified',
            'code': 401,
            'status': False,
            'en': 'Method not specified'
        },
        {
            'group': 'user',
            'name': 'access_granted',
            'code': 200,
            'status': True,
            'en': 'Access granted'
        },
        {
            'group': 'public_operations',
            'name': 'params_loaded',
            'code': 200,
            'status': True,
            'en': 'Params loaded'
        },
        {
            'group': 'public_operations',
            'name': 'params_not_loaded',
            'code': 401,
            'status': False,
            'en': 'Params not loaded'
        },
        {
            'group': 'public_operations',
            'name': 'page_limit',
            'code': 401,
            'status': False,
            'en': 'Page limit reached'
        },
        {
            'group': 'public_operations',
            'name': 'record_not_found',
            'code': 401,
            'status': False,
            'en': 'Record not found'
        },
        {
            'group': 'public_operations',
            'name': 'failed',
            'code': 401,
            'status': False,
            'en': 'Operation failed'
        },
        {
            'group': 'public_operations',
            'name': 'successful',
            'code': 200,
            'status': True,
            'en': 'Operation successful'
        },
        {
            'group': 'field_error',
            'name': 'required',
            'code': 401,
            'status': False,
            'en': 'Field %s required'
        },
        {
            'group': 'field_error',
            'name': 'null',
            'code': 401,
            'status': False,
            'en': 'Null not allowed'
        },
        {
            'group': 'field_error',
            'name': 'id_format',
            'code': 401,
            'status': False,
            'en': 'ID format is not correct'
        },
        {
            'group': 'field_error',
            'name': 'file_type',
            'code': 401,
            'status': False,
            'en': 'Type of file need to be specified in "type"'
        },
        {
            'group': 'user',
            'name': 'login_failed',
            'code': 401,
            'status': False,
            'en': 'Login information is not correct'
        },
        {
            'group': 'user',
            'name': 'logged_in',
            'code': 200,
            'status': True,
            'en': 'Logged in'
        }
    ])

insert_users()
insert_messages()
