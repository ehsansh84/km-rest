#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('/root/dev/app/')
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.options
from urls import url_patterns
from publics import set_db, consts
import socket
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(url_patterns)
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            print('Application is running on Test mode on %s:%s database name is %s...' % (IPAddr, consts.TEST_SERVER_PORT, consts.TEST_DB_NAME))
            consts.TEST_MODE = True
            set_db(consts.TEST_DB_NAME)
            app.listen(int(consts.TEST_SERVER_PORT))
        else:
            print('Wrong input')
            exit()
    else:
        print('Application is running mode on %s:%s database name is %s...' % (
        IPAddr, consts.SERVER_PORT, consts.DB_NAME))
        https_app = tornado.httpserver.HTTPServer(app)

        set_db(consts.DB_NAME)
        app.listen(int(consts.SERVER_PORT))
    tornado.ioloop.IOLoop.current().start()
