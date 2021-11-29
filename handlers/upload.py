import os
from copy import deepcopy
from datetime import datetime
from base_handler import BaseHandler
from data_templates import output
from publics import create_md5, PrintException
from consts import consts


class Upload(BaseHandler):
    def init_method(self):
        self.tokenless = True

    def post(self, *args, **kwargs):
        data = deepcopy(output)
        try:
            file_contents = self.request.files['image'][0]['body']
            file_name = self.request.files['image'][0]['filename']
            type = self.get_argument('type', '')
            file_ext = '.' + file_name.split('.')[-1]
            if not os.path.exists(consts.PDP_ROOT):
                os.mkdir(consts.PDP_ROOT)
            if not os.path.exists(consts.PDP_IMAGES):
                os.mkdir(consts.PDP_IMAGES)
            if type != '':
                if not os.path.exists(consts.PDP_IMAGES + type):
                    os.mkdir(consts.PDP_IMAGES + type)
                if not os.path.exists(consts.PDP_IMAGES + type + '/' + str(datetime.today().date())):
                    os.mkdir(consts.PDP_IMAGES + type + '/' + str(datetime.today().date()))
                filename = create_md5(str(datetime.now()) + file_name) + file_ext
                file = open('%s/%s/%s' % (consts.PDP_IMAGES + type, datetime.today().date(), filename), 'wb')
                file.write(file_contents)
                file.close()
                self.set_output('public_operations', 'successful')
                data['data']['item'] = {'link': '%s/%s/%s' % (consts.ODP_IMAGES + type, datetime.today().date(), filename)}
                print(data['data']['item'])
            else:
                self.set_output('field_error', 'file_type')
        except Exception:
            self.set_output('public_operations', 'failed')
            PrintException()
        self.write(data)
