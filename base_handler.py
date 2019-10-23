'''
KM2: change log :
1- add allow_action to prevent action in some conditions
2- self.output created to access through all methods
3- some edit in after_get and after_get_one for dates
4- fix a bug in method_access_control
5- Add auto fields to ban these kind of fields from being added or updated
6- Backward compatiblity: quick_search removed
7- Logs date bug fixed
8- Original params added to logs, useless params removed
9- If not allow action post is not performed
10- allow_action added to get method
11- Check for unknow fields in post method
12- fix doc limit error
13- Messages read from database
14- Standard base handler can be used for tokenless base handler
15- Multilingual for all fields have implemented
16- Http output has been set as an standard output
17- Print exception added here
18- Put can be done based on conditions
19- fixed Tokenless bug in put
20- after_load_params added
21- set_output returns error if message not found
22- Delete uses allow_action
23- Logical delete added
'''
import inspect
import json
from copy import deepcopy
from datetime import datetime, timedelta
from bson import ObjectId
from tornado.web import RequestHandler
from data_templates import output, log_template
from publics import consts, db, decode_token


def __enum(**named_values):
    return type('Enum', (), named_values)


Colors = __enum(BLACK=0, RED=1, LIME=2, YEOOLW=3, BLUE=4, PINK=5, CYAN=6, GRAY=7)


class BaseHandler(RequestHandler):

    def initialize(self):
        self.db = db()
        self.permissions = None
        self.start_time = datetime.now()
        self.user_id = None
        self.user_role = None
        self.id = None
        self.params = {}
        self.original_params = {}
        self.status = False
        self.status_code = 500
        self.note = ''
        self.note_group = ''  # Only usable in test mode
        self.note_id = ''     # Only usable in test mode
        self.log = []
        self.module = None
        self.logical_delete = False
        self.allow_action = True
        self.url = ''
        self.token = None
        self.locale = 'en'
        self.method = ''
        self.app_version = 0
        self.document_count = 0
        self.added_data = {}
        self.inputs = {}
        self.required = {}
        self.fields = []
        self.sort = {}
        self.doc_limit = -1
        self.auto_fields = ['create_date', 'last_update']
        self.conditions = {}
        self.output = deepcopy(output)
        self.tokenless = False
        self.multilingual = []
        self.casting = {
            'ints': [],
            'floats': [],
            'dics': [],
            'dates': [],
            'lists': [],
            'defaults': {}
        }

    def set_default_headers(self, *args, **kwargs):
        self.set_header("Access-Control-Allow-Credentials", True)
        self.set_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept")
        self.set_header("Access-Control-Allow-Headers", "content-type")
        self.set_header("Access-Control-Allow-Methods", "GET,HEAD,PUT,PATCH,POST,DELETE")
        self.set_header("Access-Control-Allow-Origin", "*")

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()

    def set_output(self, group, id, data=None):
        try:
            self.status = consts.MESSAGES[group][id]['status']
            self.set_status(consts.MESSAGES[group][id]['code'])
            self.note = consts.MESSAGES[group][id][self.locale]
            if consts.TEST_MODE:
                self.note_group = group
                self.note_id = id
            if data is not None:
                self.note = self.note % data.encode('UTF-8')

            if consts.LOG_ACTIVE:
                self.log.append({
                    'status': self.status,
                    'status_code': self.status_code,
                    'note': self.note,
                })
        except:
            self.status = False
            self.set_status(401)
            self.note = 'Server message not found: %s/%s' % (group, id)
            self.PrintException()

    def kmwrite(self):
        self.output.update({'note': self.note})
        if consts.TEST_MODE:
            self.output.update({'note_group': self.note_group, 'note_id': self.note_id})
        self.Print(self.note, Colors.LIME)
        try:
            self.write(self.output)
        except:
            self.write('An error occured when trying to write data into output: %s' % self.PrintException())

    def log_status(self, data):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        col = db()['logs']
        log = deepcopy(log_template)
        # col.da
        doc = deepcopy(self.params)
        for item in self.casting['dates']:
            if item in doc.keys():
                doc[item] = str(doc[item])
        log.update({
            'project': 'miz',
            'ip': self.request.remote_ip,
            'duration': (datetime.now() - self.start_time).total_seconds() * 1000,
            'date': datetime.now(),
            'token': self.token,
            'user_id': self.user_id,
            'doc': doc,
            'original_params': self.original_params,
            'status': self.status,
            'http_code': self.status_code,
            'output': data,
            'method': self.method,
            'url': self.request.uri,
        })
        try:
            col.insert(log)
        except:
            self.PrintException()

    def init_method(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)

    def token_validation(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            if self.token is None:
                self.set_output('user', 'token_not_received')
            else:
                token_info = decode_token(self.token)
                if token_info is None:
                    self.set_output('user', 'wrong_token')
                else:
                    tokan_date = datetime.strptime(token_info['date'], '%Y-%m-%d %H:%M:%S.%f')
                    if datetime.now() > (tokan_date -timedelta(seconds=-consts.MAX_TOKEN_DURATION)):
                        self.set_output('user', 'token_expired')
                    else:
                        self.user_id = token_info['user_id']
                        if 'app_version' in token_info:
                            if token_info['app_version'] != '':
                                self.app_version = int(token_info['app_version'].replace('.', ''))
                        self.set_output('user', 'token_validated')
        except:
            self.PrintException()
            return False
        return self.status

    def load_permissions(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            col_users = db()['users']
            user_info = col_users.find_one({'_id': ObjectId(self.user_id)})
            if user_info is None:
                self.set_output('user', 'user_not_exists')
            else:
                self.user_role = user_info['role']
                print('module: %s role: %s user_id: %s' % (self.module, user_info['role'], self.user_id))
                if self.module is None:
                    self.set_output('public_operations', 'module_not_specified')
                else:
                    col_users_roles = db()['users_roles']
                    user_role_info = col_users_roles.find_one({'name': user_info['role'], 'module': self.module})
                    print('user_role %s module %s' % (self.user_role, self.module))
                    if user_role_info is None:
                        self.set_output('user', 'access_denied')
                    else:
                        del user_role_info['_id']
                        self.permissions = user_role_info['permissions']
                        # TODO: Some kind of shit here
                        import json
                        temp = json.dumps(self.permissions)
                        temp = temp.replace('$uid', self.user_id)
                        temp = temp.replace('#', '.')
                        temp = temp.replace('@', '$')
                        self.permissions = json.loads(temp)
        except:
            self.PrintException()
            self.set_output('public_operations', 'failed')
        return self.status

    def method_access_control(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        if self.permissions is None:
            self.set_output('user', 'permission_not_defined')
        else:
            if self.method == '':
                self.set_output('user', 'method_not_specified')
            elif self.method in self.permissions['allow']:
                self.set_output('user', 'access_granted')
            else:
                self.set_output('user', 'access_denied')
        return self.status

    def load_params(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            if self.method == '':
                self.set_output('user', 'method_not_specified')
            elif self.method == 'get':
                self.params = {k: self.get_argument(k) for k in self.request.arguments}
                self.original_params = deepcopy(self.params)
                if 'fields' in self.params:
                    self.fields = json.loads(self.params['fields'])
                    del self.params['fields']
                if 'sort' in self.params:
                    self.sort = json.loads(self.params['sort'])
                    del self.params['sort']
            elif self.method in ['post', 'put', 'delete']:
                self.params = json.loads(self.request.body)
                self.original_params = deepcopy(self.params)
            if 'locale' in self.params:
                self.locale = self.params['locale']
                del self.params['locale']
            if 'token' in self.params:
                self.token = self.params['token']
                del self.params['token']

            if 'get' in self.inputs:
                self.inputs['get'].extend(['page', 'page_size', 'conditions'])
            else:
                # self.Print(self.inputs)
                self.inputs['get'] = ['page', 'page_size', 'conditions']
            if 'put' in self.inputs:
                self.inputs['put'].append('id')
            else:
                self.inputs['put'] = ['id']

            if 'delete' in self.inputs:
                self.inputs['delete'].extend(['id', 'conditions'])
            else:
                self.inputs['delete'] = ['id', 'conditions']
            self.set_output('public_operations', 'params_loaded')
            # self.Print(self.params)
        except:
            self.PrintException()
            self.set_output('public_operations', 'params_not_loaded')
            return False
        self.after_load_params()
        return True

    def after_load_params(self):
        return True

    def get_validation_check(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            if 'get' in self.required:
                for item in self.required[self.method]:
                    if item not in self.params.keys():
                        self.set_output('field_error', 'required', item)
                        return False
        except:
            self.PrintException()
            return False
        return True

    def post_validation_check(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            if 'post' in self.required:
                for item in self.required[self.method]:
                    if item not in self.params.keys():
                        self.set_output('field_error', 'required', item)
                        return False
        except:
            self.PrintException()
            return False
        return True

    def put_validation_check(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            if 'put' in self.required:
                for item in self.required[self.method]:
                    if item not in self.params.keys():
                        self.set_output('field_error', 'required', item)
                        return False
        except:
            self.PrintException()
            return False
        return True

    def delete_validation_check(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        if not 'id' in self.params.keys():
            self.set_output('field_error', 'delete_id')
            return False
        return True

    def data_casting(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            # self.Print(self.method)
            self.casting['ints'].extend(['page', 'page_size'])
            self.casting['dics'].extend(['conditions'])
            self.casting['lists'].extend(['fields'])
            self.casting['dates'].extend(['create_date', 'last_update'])
            if self.method in ['post', 'put']:
                pass
            for item in self.params.keys():
                if item in self.casting['ints']:
                    self.params[item] = int(self.params[item])
                elif item in self.casting['dics']:
                    if self.method == 'get':
                        self.params[item] = json.loads(self.params[item])
                elif item in self.casting['floats']:
                    self.params[item] = float(self.params[item])
        except:
            self.PrintException()
            self.set_output('field_error', 'casting', item)
            return False
        return True

    def get_init(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        if 'page' not in self.params: self.params['page'] = 1
        if 'page_size' not in self.params: self.params['page_size'] = consts.page_size
        if 'sort' not in self.params: self.params['sort'] = {}
        if 'quick_search' not in self.params: self.params['quick_search'] = {}
        if 'conditions' not in self.params: self.params['conditions'] = {}
        if 'fields' not in self.params: self.params['fields'] = {}

    def before_get(self):
        return True

    def pre_get(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            if self.module is None:
                self.module = self.request.uri.split('/')[2].split('?')[0]
            self.init_method()
            if self.load_params():
                if not self.tokenless:
                    if self.token_validation():
                        if self.load_permissions():
                            self.method_access_control()
                if self.status:
                    if self.get_validation_check():
                        if self.data_casting():
                            if 'conditions' in self.params:
                                self.conditions = self.params['conditions']
                                if 'id_list' in self.conditions.keys():
                                    id_list = []
                                    for item in self.conditions['id_list']:
                                        id_list.append(ObjectId(item))
                                    self.conditions['_id'] = {'$in': id_list}
                                    del self.conditions['id_list']
                                for k, v in self.conditions.items():
                                    if k in self.multilingual:
                                        self.conditions[k + '.' + self.locale] = self.conditions[k]
                                        del self.conditions[k]
                                del self.params['conditions']
                            if not self.tokenless:
                                self.add_user_data()
                            return self.before_get()
        except:
            self.PrintException()
            self.set_output('public_operations', 'failed')
        return False

    def set_default_values(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        for item in self.casting['defaults'].keys():
            try:
                if item not in self.params:
                    self.params[item] = self.casting['defaults'][item]
            except:
                self.PrintException()

    def add_user_data(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            if self.method in ['get']:
                self.conditions.update(self.permissions[self.method])
                if 'doc_limit' in self.permissions: self.doc_limit = self.permissions['doc_limit']
            elif self.method == 'post':
                for item in self.params.keys():
                    if item in self.auto_fields:
                        del self.params[item]
                self.params.update(self.permissions[self.method])
            elif self.method == 'delete':
                self.params.update(self.permissions[self.method])
            elif self.method == 'put':
                for item in self.params.keys():
                    if item in self.auto_fields:
                        del self.params[item]
                self.params.update(self.permissions[self.method]['set'])
        except:
            self.PrintException()

    def prepare_item(self, document):
        try:
            if '_id' in document:
                document['id'] = str(document['_id'])
                del document['_id']
            for k, v in document.items():
                if 'dates' in self.casting:
                    if k in self.casting['dates']:
                        document[k] = str(v)
                if 'multilingual' != []:
                    if k in self.multilingual:
                        if self.locale in document[k]:
                            document[k] = document[k][self.locale]
                        else:
                            document[k] = consts.MESSAGES['field_error']['language_not_defined'][self.locale]
        except:
            self.PrintException()
        return document

    def after_get(self, dataset):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        temp = []
        try:
            for item in dataset:
                temp.append(self.prepare_item(item))
        except:
            self.PrintException()
        return temp

    def after_get_one(self, document):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        return self.prepare_item(document)

    def get(self, id=None, *args, **kwargs):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            self.method = 'get'
            if self.pre_get():
                # TODO: Remove this code after some time, only for null values sent by retards
                if self.allow_action:
                    has_null = False
                    for k, v in self.params.items():
                        if v in [None, 'null']:
                            self.set_output('field_error', 'null')
                            has_null = True
                    if not has_null:
                        col = db()[self.module]
                        fields_dic = {}
                        for item in self.fields:
                            fields_dic[item] = 1

                        if id is None:
                            self.get_init()
                            if self.doc_limit > -1 and self.params['page'] * self.params['page_size'] > self.doc_limit:
                                self.set_output('public_operations', 'page_limit')
                            else:
                                if self.sort == {}:
                                    if fields_dic == {}:
                                        results = col.find(self.conditions).skip((self.params['page'] - 1) * self.params['page_size']).limit(self.params['page_size'])
                                    else:
                                        results = col.find(self.conditions, fields_dic).skip((self.params['page'] - 1) * self.params['page_size']).limit(self.params['page_size'])
                                else:
                                    sort_conditions = []
                                    for k, v in self.sort.items():
                                        sort_conditions.append((k, v))
                                    if fields_dic == {}:
                                        results = col.find(self.conditions).skip((self.params['page'] - 1) * self.params['page_size'])\
                                            .limit(self.params['page_size']).sort(sort_conditions)
                                    else:
                                        results = col.find(self.conditions, fields_dic).skip((self.params['page'] - 1) * self.params['page_size'])\
                                            .limit(self.params['page_size']).sort(sort_conditions)
                                self.document_count = results.count()
                                results = self.after_get(results)
                                self.output['data']['count'] = self.document_count
                                self.output['data']['list'] = results
                                self.set_output('public_operations', 'successful')
                        else:
                            try:
                                # TODO: Shit happend, I should do something for this
                                object_id = ObjectId(id) if self.module != 'achievements' else id
                                if fields_dic == {}:
                                    results = col.find_one({'_id': object_id})
                                else:
                                    results = col.find_one({'_id': object_id}, fields_dic)
                                if results is None:
                                    self.set_output('public_operations', 'record_not_found')
                                else:
                                    self.output['data']['item'] = self.after_get_one(results)
                                    self.output['count'] = 1
                                    self.set_output('public_operations', 'successful')
                            except:
                                self.PrintException()
                                self.set_output('field_error', 'id_format')
        except:
            self.PrintException()
            self.set_output('public_operations', 'failed')
        if consts.LOG_ACTIVE:
            self.log_status(self.output)
        self.kmwrite()

    def pre_post(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.BLUE)
        try:
            self.module = self.request.uri.split('/')[2].split('?')[0]
            self.init_method()
            if self.load_params():
                if not self.tokenless:
                    if self.token_validation():
                        if self.load_permissions():
                            if self.method_access_control():
                                self.add_user_data()
                if self.status:
                    if self.post_validation_check():
                        if self.data_casting():
                            self.set_default_values()
                            if self.before_post():
                                return True
        except:
            self.PrintException()
        return False

    def before_post(self):
        return True

    def before_put(self):
        return True

    def post(self, *args, **kwargs):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            self.method = 'post'
            if self.pre_post():
                if self.allow_action:
                    # TODO: Remove this code after some time, only for null values sent by retards
                    validated = True
                    new_params = deepcopy(self.params)
                    for k, v in self.params.items():
                        if v in [None, 'null']:
                            self.set_output('field_error', 'null')
                            validated = False
                            # break
                        if k in self.multilingual:
                            new_params[k] = {}
                            new_params[k][self.locale] = self.params[k]
                    self.params = deepcopy(new_params)
                    if validated:
                        self.params.update(self.added_data)
                        col = db()[self.module]
                        self.params['create_date'] = datetime.now()
                        self.params['last_update'] = datetime.now()
                        id = str(col.insert(self.params))
                        self.id = id
                        self.output['data']['item']['id'] = id
                        self.set_output('public_operations', 'successful')
                    self.after_post()

            if consts.LOG_ACTIVE:
                self.log_status(self.output)
        except:
            self.PrintException()
            self.set_output('public_operations', 'failed')
        self.kmwrite()

    def after_post(self):
        return True

    def pre_put(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            self.module = self.request.uri.split('/')[2].split('?')[0]
            self.init_method()
            if self.load_params():
                if not self.tokenless:
                    if self.token_validation():
                        if self.load_permissions():
                            if self.method_access_control():
                                self.add_user_data()
            if self.status:
                if self.put_validation_check():
                    if self.data_casting():
                        if self.before_put():
                            return True
        except:
            self.PrintException()
        return False

    def after_put(self):
        return True

    def put(self, *args, **kwargs):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            self.method = 'put'
            self.module = self.request.uri.split('/')[2].split('?')[0]
            if self.pre_put():
                # TODO: Remove this code after some time, only for null values sent by retards
                if self.allow_action:
                    has_null = False
                    for k, v in self.params.items():
                        if v in [None, 'null']:
                            self.set_output('field_error', 'null')
                            has_null = True
                        if k in self.multilingual:
                            self.params[k + '.' + self.locale] = v
                            del self.params[k]

                    for k, v in self.conditions.items():
                        if v in [None, 'null']:
                            self.set_output('field_error', 'null')
                            has_null = True
                            break
                    if not has_null:
                        if 'create_date' in self.params: del self.params['create_date']
                        self.params['last_update'] = datetime.now()
                        col = db()[self.module]
                        if self.conditions == {}:
                            id = self.params['id']
                            del self.params['id']
                            try:
                                id = ObjectId(id) if self.module != 'achievements' else id
                                query = {'_id': id}
                            except:
                                self.set_output('field_error', 'id_format')
                                self.PrintException()
                                return
                        else:
                            query = self.conditions
                        if not self.tokenless:
                            if 'put' in self.permissions:
                                query.update(self.permissions['put']['query'])
                        results = col.update_one(query, {'$set': self.params}).raw_result

                        if self.conditions == {}:
                            self.params['id'] = id
                        if results['nModified'] > 0:
                            self.set_output('public_operations', 'successful')
                        elif results['updatedExisting']:
                            self.set_output('public_operations', 'update_failed')
                        else:
                            self.set_output('public_operations', 'record_not_found')
            if consts.LOG_ACTIVE:
                self.log_status(self.output)
            self.after_put()
        except:
            self.PrintException()
            self.set_output('public_operations', 'failed')
            self.Print(self.note, Colors.RED)
        self.kmwrite()

    def pre_delete(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        self.module = self.request.uri.split('/')[2].split('?')[0]
        try:
            self.init_method()
            if self.load_params():
                if not self.tokenless:
                    if self.token_validation():
                        if self.load_permissions():
                            self.method_access_control()
                if self.status:
                    if self.delete_validation_check():
                        if self.data_casting():
                            if 'conditions' in self.params:
                                self.conditions = self.params['conditions']
                                del self.params['conditions']
                            if not self.tokenless:
                                self.add_user_data()
                            if self.before_delete():
                                return True
        except:
            self.PrintException()
        return False

    def before_delete(self):
        return True

    def delete(self, *args, **kwargs):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        try:
            self.method = 'delete'
            self.module = self.request.uri.split('/')[2].split('?')[0]
            if self.pre_delete():
                if self.allow_action:
                    col = db()[self.module]
                    if self.logical_delete:
                        results = col.update_one({'_id': ObjectId(self.params['id'])},
                                                     {'$set': {'deleted': True}}).raw_result
                        if results['nModified'] == 1:
                            self.set_output('public_operations', 'successful')
                        else:
                            self.set_output('public_operations', 'record_not_found')
                    else:
                        if self.conditions == {}:
                            self.conditions = {'_id': ObjectId(self.params['id'])}
                        results = col.remove(self.conditions)
                        if results['n'] == 1:
                            self.set_output('public_operations', 'successful')
                        else:
                            self.set_output('public_operations', 'record_not_found')
                    self.after_delete()
            if consts.LOG_ACTIVE:
                self.log_status(self.output)
        except:
            self.PrintException()
            self.set_output('public_operations', 'failed')
        self.kmwrite()



    def after_delete(self):
        return True

    def Print(self, text, color=None):
        try:
            print('\033[1;3'+str(color)+'m'+str(text)+'\033[1;m')
        except:
            print('\033[1;3'+str(color)+'m'+text.encode('utf-8')+'\033[1;m')

    def PrintException(self):
        import linecache
        import sys
        try:
            log = []
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            linecache.checkcache(filename)
            line = linecache.getline(filename, lineno, f.f_globals)
            log.append(filename)
            log.append(str(lineno))
            log.append(line.strip())
            log.append("'" + str(exc_obj) + "'")
            self.Print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj), Colors.RED)
            return 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)
        except:
            print('An error in error handler!')
