import json
from copy import deepcopy
from datetime import datetime, timedelta
from bson import ObjectId
from tornado.web import RequestHandler
from data_templates import output, log_template
from publics import db, decode_token
from consts import consts
from log_tools import log


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
            self.status_code = consts.MESSAGES[group][id]['code']
            if data is not None:
                self.note = self.note % data.encode('UTF-8')

            if consts.LOG_ACTIVE:
                self.log.append({
                    'status': self.status,
                    'status_code': self.status_code,
                    'note': self.note,
                })
        except Exception as e:
            log.error(f'Error {str(e)}')
            self.status = False
            self.set_status(401)
            self.note = 'Server message not found: %s/%s' % (group, id)

    def kmwrite(self):
        self.output.update({'note': self.note})
        # self.Print(self.note, Colors.LIME)
        try:
            self.write(self.output)
            if consts.LOG_ACTIVE:
                self.log_status()
        except Exception as e:
            self.write(f'An error occured when trying to write data into output: {str(e)}')
            self.write('<hr/>')
            self.write(str(self.output))

    def success(self):
        self.set_output('public_operations', 'successful')

    def fail(self):
        self.set_output('public_operations', 'failed')

    def log_status(self):
        col = db()['logs']
        log = deepcopy(log_template)
        doc = deepcopy(self.params)
        for item in self.casting['dates']:
            if item in doc.keys():
                doc[item] = str(doc[item])
                print('X-Real-ip')
                print(self.request.remote_ip)

        log.update({
            'project': 'miz',
            'ip': self.request.headers['X-Real-IP'] if 'X-Real-IP' in self.request.headers else self.request.remote_ip,
            'duration': (datetime.now() - self.start_time).total_seconds() * 1000,
            'date': datetime.now(),
            'date_only': str(datetime.now().date()),
            'module': self.module,
            'module_id': self.id,
            'token': self.token,
            'user_id': self.user_id,
            'doc': doc,
            'original_params': self.original_params,
            'status': self.status,
            'http_code': self.status_code,
            'output': self.output,
            'method': self.request.method,
            'url': self.request.uri,
        })
        try:
            col.insert(log, check_keys=False)
        except Exception as e:
            log.error(f'Error {str(e)}')

    def init_method(self):
        pass

    def token_validation(self):
        try:
            if self.token is None:
                self.user_id = '5dbfb57dbbe873941f0ac431'
                # self.set_output('user', 'token_not_received')
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
        except Exception as e:
            log.error(f'Error {str(e)}')
            return False
        return self.status

    def load_permissions(self):
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
        except Exception as e:
            log.error(f'Error {str(e)}')
            self.fail()
        return self.status

    def method_access_control(self):
        try:
            if self.permissions is None:
                self.set_output('user', 'permission_not_defined')
            else:
                #TODO: better to insert uppercase in db
                if self.request.method.lower() in self.permissions['allow']:
                    self.set_output('user', 'access_granted')
                else:
                    self.set_output('user', 'access_denied')
        except Exception as e:
            log.error(f'Failed {str(e)}')
            self.fail()
        return self.status

    def load_params(self):
        try:
            if self.request.method == 'GET':
                self.params = {k: self.get_argument(k) for k in self.request.arguments}
                self.original_params = deepcopy(self.params)
                if 'fields' in self.params:
                    self.fields = json.loads(self.params['fields'])
                    del self.params['fields']
                if 'sort' in self.params:
                    self.sort = json.loads(self.params['sort'])
                    del self.params['sort']
            elif self.request.method in ['POST', 'PUT', 'DELETE']:
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
                self.inputs['get'] = ['page', 'page_size', 'conditions']
            if 'put' in self.inputs:
                self.inputs['put'].append('id')
            else:
                self.inputs['put'] = ['id']

            if 'delete' in self.inputs:
                self.inputs['delete'].extend(['id', 'conditions'])
            else:
                self.inputs['delete'] = ['id', 'conditions']
            if 'conditions' in self.params:
                temp_conditions = self.params['conditions']
                del self.params['conditions']
                for k, v in temp_conditions.items():
                    if v in [None, 'null']:
                        self.set_output('field_error', 'null')
                        return True
                self.conditions = temp_conditions
            params = {}
            for k, v in self.params.items():
                if v in [None, 'null']:
                    self.set_output('field_error', 'null')
                    return False
                if k in self.multilingual:
                    params[k + '.' + self.locale] = v
                else:
                    params[k] = v
                self.params = params
            self.set_output('public_operations', 'params_loaded')
        except Exception as e:
            log.error(f'Error {str(e)}')
            self.set_output('public_operations', 'params_not_loaded')
            return False
        self.after_load_params()
        return True

    def after_load_params(self):
        return True

    def get_validation_check(self):
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
        try:
            if 'post' in self.required:
                for item in self.required[self.method]:
                    if item not in self.params.keys():
                        self.set_output('field_error', 'required', item)
                        return False
        except Exception as e:
            log.error(f'Error {str(e)}')
            return False
        return True

    def put_validation_check(self):
        try:
            if 'put' in self.required:
                for item in self.required[self.method]:
                    if item not in self.params.keys():
                        self.set_output('field_error', 'required', item)
                        return False
        except Exception as e:
            log.error(f'Error {str(e)}')
            return False
        return True

    def delete_validation_check(self, id):
        if id is None:
            self.set_output('field_error', 'delete_id')
            return False
        return True

    def data_casting(self):
        try:
            self.casting['ints'].extend(['page', 'page_size'])
            self.casting['dics'].extend(['conditions'])
            self.casting['lists'].extend(['fields'])
            self.casting['dates'].extend(['create_date', 'last_update'])
            if self.request.method in ['POST', 'PUT']:
                pass
            for item in self.params.keys():
                if item in self.casting['ints']:
                    self.params[item] = int(self.params[item])
                elif item in self.casting['dics']:
                    if self.request.method == 'GET':
                        self.params[item] = json.loads(self.params[item])
                elif item in self.casting['floats']:
                    self.params[item] = float(self.params[item])
        except Exception as e:
            log.error(f'Error {str(e)}')
            self.set_output('field_error', 'casting', item)
            return False
        return True

    def get_init(self):
        if 'page' not in self.params: self.params['page'] = 1
        if 'page_size' not in self.params: self.params['page_size'] = consts.page_size
        if 'sort' not in self.params: self.params['sort'] = {}
        if 'quick_search' not in self.params: self.params['quick_search'] = {}
        if 'conditions' not in self.params: self.params['conditions'] = {}
        if 'fields' not in self.params: self.params['fields'] = {}

    def pre_get(self):
        try:
            if self.module is None:
                self.module = self.request.uri.split('/')[2].split('?')[0]
            self.init_method()
            if self.load_params():
                if not self.tokenless:
                    if self.token_validation():
                        if self.load_permissions():
                            if self.method_access_control():
                                self.add_user_data()
                    if self.token_validation():
                        if self.load_permissions():
                            self.method_access_control()
                if self.status:
                    if self.get_validation_check():
                        if self.data_casting():
                            if 'conditions' in self.params:
                                self.conditions = self.params['conditions']
                                conditions = {}
                                if 'id_list' in self.conditions.keys():
                                    id_list = []
                                    for item in self.conditions['id_list']:
                                        id_list.append(ObjectId(item))
                                    conditions['_id'] = {'$in': id_list}
                                    del self.conditions['id_list']
                                for k, v in self.conditions.items():
                                    if k in self.multilingual:
                                        conditions[k + '.' + self.locale] = self.conditions[k]
                                    else:
                                        conditions[k] = v
                                self.conditions = conditions
                                import json
                                del self.params['conditions']
                            if not self.tokenless:
                                self.add_user_data()
                            return self.before_get()
        except Exception as e:
            log.error(f'Error {str(e)}')
            self.fail()
        return False

    def set_default_values(self):
        for item in self.casting['defaults'].keys():
            try:
                if item not in self.params:
                    self.params[item] = self.casting['defaults'][item]
            except Exception as e:
                log.error(f'Error {str(e)}')

    def add_user_data(self):
        try:
            if self.request.method in ['GET']:
                self.conditions.update(self.permissions[self.method])
                if 'doc_limit' in self.permissions: self.doc_limit = self.permissions['doc_limit']
            elif self.request.method == 'POST':
                for item in self.params.keys():
                    if item in self.auto_fields:
                        del self.params[item]
                self.params.update(self.permissions[self.request.method])
            elif self.request.method == 'DELETE':
                self.params.update(self.permissions[self.request.method])
            elif self.request.method == 'PUT':
                temp_params = {}
                for item in self.params.keys():
                    if item not in self.auto_fields:
                        temp_params[item] = self.params[item]
                self.params = temp_params
                self.params.update(self.permissions[self.request.method]['set'])
        except Exception as e:
            log.error(f'Error {str(e)}')

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
        except Exception as e:
            log.error(f'Error {str(e)}')
        return document

    def prepare_dataset(self, dataset):
        data_list = []
        try:
            for document in dataset:
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
                data_list.append(document)
        except Exception as e:
            log.error(f'Error {str(e)}')
        return data_list

    def after_get(self, dataset):
        temp = []
        try:
            for item in dataset:
                temp.append(self.prepare_item(item))
        except Exception as e:
            log.error(f'Error {str(e)}')
        return temp

    def after_get_one(self, document):
        return self.prepare_item(document)

    def get(self, id=None, *args, **kwargs):
        try:
            self.method = 'get'
            self.id = id
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
                                # self.set_output('public_operations', 'successful')
                                self.success()
                        else:
                            try:
                                # TODO: Shit happend, I should do something for this
                                object_id = ObjectId(id) if self.module != 'achievements' else id
                                # self.id = id
                                if fields_dic == {}:
                                    results = col.find_one({'_id': object_id})
                                else:
                                    results = col.find_one({'_id': object_id}, fields_dic)
                                if results is None:
                                    self.set_output('public_operations', 'record_not_found')
                                else:
                                    self.output['data']['item'] = self.after_get_one(results)
                                    self.output['count'] = 1
                                    # self.set_output('public_operations', 'successful')
                                    self.success()
                            except:
                                self.set_output('field_error', 'id_format')
        except:
            self.fail()
        self.kmwrite()

    def post(self,id=None, *args, **kwargs):
        try:
            if self.http_init(id):
                if self.before_post():
                    if self.allow_action:
                        # TODO: Remove this code after some time, only for null values sent by retards
                        new_params = deepcopy(self.params)
                        self.params = deepcopy(new_params)
                        self.params.update(self.added_data)
                        col = db()[self.module]
                        self.params['create_date'] = datetime.now()
                        self.params['last_update'] = datetime.now()
                        self.id = col.insert(self.params)
                        self.output['data']['item']['id'] = str(self.id)
                        self.success()
                    self.after_post()
        except:
            self.fail()
        self.kmwrite()

    def http_init(self, id):
        self.module = self.request.uri.split('/')[2].split('?')[0]
        #TODO: check for id format
        if id is not None:
            self.id = ObjectId(id)
        self.init_method()
        if not self.load_params():
            return False
        log.debug('Params loaded')
        self.data_casting()
        log.debug('Data casted')
        if not self.tokenless:
            log.debug("It's not tokenless")
            if not (self.token_validation() and self.load_permissions() and self.method_access_control() and self.add_user_data()):
                return False
        return True

    def put(self,id=None, *args, **kwargs):
        try:
            if self.http_init(id):
                log.debug("http_init done!")
                if self.put_validation_check():
                    log.debug("put_validation_check done!")
                    if self.before_put():
                        log.debug("before_put done!")
                        # TODO: Remove this code after some time, only for null values sent by retards
                        if self.allow_action:
                            log.debug("action allowed!")
                            if 'create_date' in self.params: del self.params['create_date']
                            self.params['last_update'] = datetime.now()
                            col = db()[self.module]
                            query = {}
                            results = ''
                            if not self.tokenless:
                                if 'PUT' in self.permissions:
                                    query.update(self.permissions['PUT']['query'])
                            if self.id is None:
                                if self.conditions == {}:
                                    log.error('No ID and No conditions!')
                                    self.fail()
                                    #TODO: end this
                                else:
                                    query = self.conditions
                                    log.debug(self.conditions)
                                    results = col.update(query, {'$set': self.params}, multi=True)
                            else:
                                query = {'_id': self.id}
                                log.debug(query)
                                results = col.update_one(query, {'$set': self.params}).raw_result
                            log.debug(results)
                            if results != '':
                                if results['nModified'] > 0:
                                    self.success()
                                elif results['updatedExisting']:
                                    self.fail()
                                else:
                                    self.set_output('public_operations', 'record_not_found')
            else:
                log.error('An error happend in pre_put level!')
            self.after_put()
        except:
            self.fail()
        self.kmwrite()

    def delete(self, id=None, *args, **kwargs):
        try:
            if self.http_init(id):
                if self.before_delete():
                    if self.allow_action:
                        col = db()[self.module]
                        log.info(f"ID: {self.id}")
                        if self.logical_delete:
                            results = col.update_one({'_id': self.id},
                                                         {'$set': {'deleted': True}}).raw_result
                            if results['nModified'] == 1:
                                self.success()
                            else:
                                self.set_output('public_operations', 'record_not_found')
                        else:
                            query = {}
                            results = ''
                            if not self.tokenless:
                                if 'DELETE' in self.permissions:
                                    query.update(self.permissions['DELETE'])
                            if self.id is None:
                                if self.conditions == {}:
                                    log.error('No ID and No conditions!')
                                    self.fail()
                                    #TODO: end this
                                else:
                                    query = self.conditions
                                    log.debug(self.conditions)
                                    results = col.remove(query)
                            else:
                                query = {'_id': self.id}
                                log.debug(query)
                                results = col.delete_one(query).raw_result
                            log.debug(f"results=> {results}")
                            if results != '':
                                if results['n'] >= 1:
                                    self.success()
                                else:
                                    self.set_output('public_operations', 'record_not_found')
                        self.after_delete()
        except:
            self.fail()
        self.kmwrite()

    def before_delete(self):
        return True

    def after_delete(self):
        return True

    def after_post(self):
        return True

    def after_put(self):
        return True

    def before_post(self):
        return True

    def before_put(self):
        return True

    def before_get(self):
        return True
