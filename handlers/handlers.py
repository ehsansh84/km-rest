from base_handler import BaseHandler


class SampleClass(BaseHandler):
    def init_method(self):
        self.required = {
            'post': ['field1']
        }
        self.multilingual = ['field2']
        self.inputs = {
            'post': ['field1', 'field2', 'field3'],
            'put': ['field1', 'field2', 'field3']
        }

