#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
sys.path.append('/root/dev/app/')
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.options
from urls import url_patterns
from publics import set_db
from consts import consts
import socket
from publics import load_messages, load_notifications

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(url_patterns)
    https_app = tornado.httpserver.HTTPServer(app)
    print('YES')
    if os.getenv('MONGO'):
        print('NO')
        consts.MESSAGES = load_messages()
        consts.NOTIFICATIONS = load_notifications()
        app.listen(int(consts.SERVER_PORT))
        tornado.ioloop.IOLoop.current().start()
    else:
        print('Fatal error: You must supply MONGO environment variable with mongodb docker name')
