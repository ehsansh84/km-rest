#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('/root/dev/miz/')
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.options
from urls import url_patterns
from publics import set_db, consts
import socket
import os
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(url_patterns)
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            print('Miz is running on Test mode on %s:%s database name is %s...' % (IPAddr, consts.TEST_SERVER_PORT, consts.TEST_DB_NAME))
            consts.TEST_MODE = True
            set_db(consts.TEST_DB_NAME)
            app.listen(int(consts.TEST_SERVER_PORT))
        elif sys.argv[1] == 'ssl':
            print('Miz is running on SSL mode on %s:%s database name is %s...' % (IPAddr, consts.SSL_SERVER_PORT, consts.DB_NAME))
            settings = dict(
            ssl_options = {
                              "certfile": "/var/www/cert/cert",
                              "keyfile": os.path.join("/var/www/cert/pkey"),
                          },
            )
            https_app = tornado.httpserver.HTTPServer(app, **settings)
            set_db(consts.DB_NAME)
            app.listen(int(consts.SSL_SERVER_PORT))
        else:
            print('Wrong input')
            exit()
    else:
        print('Miz is running mode on %s:%s database name is %s...' % (
        IPAddr, consts.SERVER_PORT, consts.DB_NAME))
        https_app = tornado.httpserver.HTTPServer(app)

        set_db(consts.DB_NAME)
        app.listen(int(consts.SERVER_PORT))
    tornado.ioloop.IOLoop.current().start()
