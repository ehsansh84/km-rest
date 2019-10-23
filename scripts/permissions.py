from publics import db, set_db
set_db('rest')

col_users_roles = db()['users_roles']
col_users_roles.drop()
col_users_roles.insert_many([
    {
        'name': 'admin',
        'module': 'users',
        'permissions': {
            'allow': ['get'],
            'get': {}
        },
    },
    {
        'name': 'user',
        'module': 'profile',
        'permissions': {
            'allow': ['get', 'put'],
            'get': {'user_id':'$uid'},
            'put': {
                'query': {'user_id':'$uid'},
                'set': {}

            },
        },
    },

])
