import inspect
from datetime import datetime
from base_handler import BaseHandler, Colors

from publics import consts
from math import sin, cos, sqrt, atan2, radians


class Home(BaseHandler):
    def init_method(self):
        self.Print('%s fired' % inspect.stack()[0][3], Colors.GRAY)
        self.multilingual = ['name']
        self.required = {
            'get': ['lat', 'lon']
        }
        self.inputs = {
            'post': [],
            'put': [],
        }
        self.casting['floats'] = ['lat', 'lon']
        self.casting['dates'] = ['from_date', 'to_date']
        self.module = 'home'

    def before_get(self):
        try:
            # print 1
            self.allow_action = False
            recent_searches = []
            billboards = []
            col_categories = self.db['categories']
            col_tags = self.db['tags']
            top_tags = self.after_get(col_tags.find({'default': True, 'confirmed': True}).limit(5))
            col_search_history = self.db['search_history']
            search_history = self.after_get(col_search_history.find({'user_id': self.user_id}).limit(5).sort('last_update', -1))

            top_categories = []
            results = col_categories.find({'default': True}).limit(6)
            for item in results:
                temp = {}
                try:
                    temp['id'] = str(item['_id'])
                    temp['name'] = item['name'][self.locale]
                    temp['image'] = item['image'] if 'image' in item else ''
                    top_categories.append(temp)
                except:
                    self.PrintException()
            col_billboards = self.db['billboards']
            results = col_billboards.find({'location':
                                    {
                                        "$near": {
                                            "$geometry": {
                                                "type": "Point",
                                                "coordinates": [self.params['lon'], self.params['lat']]
                                            },
                                            "$maxDistance": 10000
                                        }
                                    },
                                    'from_date': {'$lte': datetime.now()},
                                    'to_date': {'$gte': datetime.now()},
                                 }).limit(consts.MAX_HOME_BILLBOARD_COUNT)
            for item in results:
                item = self.prepare_item(item)
                # item['title'] = item['title'][self.locale]
                # item['description'] = item['description'][self.locale]
                item['title'] = '' if self.locale not in item['title'] else item['title'][self.locale]
                item['description'] = '' if self.locale not in item['description'] else item['description'][self.locale]
                R = 6373.0
                lat1 = radians(item["location"]['coordinates'][1])
                lon1 = radians(item["location"]['coordinates'][0])
                lat2 = radians(self.params['lat'])
                lon2 = radians(self.params['lon'])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                distance = R * c
                # TODO: Maybe there is a bug for multiple values
                if (distance * 1000) < item['radius']:
                    link = '' if 'link' not in item else item['link']
                    billboards.append({'logo': item['logo'],
                                       'service_id': item['service_id'],
                                       'title': item['title'],
                                       'description': item['description'],
                                       'link': link,
                                       })
            # print '22222222222222222222222222'

            if len(billboards) == 0:
                results = col_billboards.find({'default': True})
                # results = self.after_get(results)
                # print '1111111111111111111111111111'
                temp = []
                for item in results:
                    item = self.prepare_item(item)
                    item['title'] = '' if self.locale not in item['title'] else item['title'][self.locale]
                    item['description'] = '' if self.locale not in item['description'] else item['description'][self.locale]
                    # item['description'] = item['description'][self.locale]
                    temp.append(item)


                billboards = temp
                self.Print(billboards, Colors.RED)

            col_recommendations = self.db['recommendations']
            recommendations = self.after_get(col_recommendations.find())

            self.output['data']['item'] = {
                'billboards': billboards,
                'recent_searches': recent_searches,
                'top_tags': top_tags,
                'search_history': search_history,
                'recommendations': recommendations,
                'top_categories': top_categories
            }
            self.set_output('public_operations', 'successful')
        except:
            self.PrintException()
